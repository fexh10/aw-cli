import asyncio
import re
from pathlib import Path
from httpx import AsyncClient
from rich.progress import Progress, BarColumn, TextColumn, TaskID, DownloadColumn, TransferSpeedColumn
from . import utilities as ut
from .anime import Anime
from .providers import Provider
from . import streams

from functools import lru_cache

# Numero di connessioni parallele usate di default per scaricare un singolo
# episodio. Molti CDN limitano la banda per-connessione: scaricare lo stesso
# file a segmenti con più connessioni aggira quel limite. Sovrascrivibile
# tramite l'opzione "connections-per-download" nel file di configurazione.
DEFAULT_CONNECTIONS = 4

# Dimensione dei blocchi letti dallo stream. 1 MB riduce drasticamente
# l'overhead rispetto a letture da 1 KB su file di centinaia di MB.
CHUNK_SIZE = 1024 * 1024

def _segment_ranges(total: int, connections: int) -> list[tuple[int, int]]:
    """
    Divide un download in intervalli byte inclusivi, evitando segmenti vuoti.
    """
    if total <= 0 or connections <= 0:
        return []

    connections = min(connections, total)
    base_size, remainder = divmod(total, connections)
    ranges = []
    start = 0
    for i in range(connections):
        size = base_size + (1 if i < remainder else 0)
        end = start + size - 1
        ranges.append((start, end))
        start = end + 1
    return ranges

def _valid_partial_response(response, start: int, end: int, total: int) -> bool:
    """
    Verifica che il server abbia rispettato il Range richiesto.
    """
    if response.status_code != 206:
        return False

    content_range = response.headers.get("content-range", "")
    match = re.fullmatch(r"bytes (\d+)-(\d+)/(\d+|\*)", content_range)
    if not match:
        return False

    actual_start = int(match.group(1))
    actual_end = int(match.group(2))
    actual_total = match.group(3)
    return (
        actual_start == start
        and actual_end == end
        and (actual_total == "*" or int(actual_total) == total)
    )

@lru_cache
def path(create: bool = True) -> Path:
    """
    Restituisce il percorso di download dell'anime, a seconda del sistema operativo in uso.
    Se create è True (valore predefinito) e il percorso non esiste, viene creato.

    Args:
        create (bool, optional): se impostato a True, crea il percorso se non esiste. Valore predefinito: True.

    Returns:
        Path: il percorso di download dell'anime.
    """

    if (ut.os_name == "Android"):
        path = Path("/sdcard/Movies/Anime")
    else:
        path = Path.home() / "Videos/Anime"

    if create:
        path.mkdir(parents=True, exist_ok=True)
    return path

def episodes(anime: Anime, episodes: list[Anime.Episode], provider: Provider) -> None:
    """
    Scarica più episodi in modo concorrente (max concurrent_downloads).

    Args:
        anime (Anime): l'anime di cui scaricare gli episodi.
        episodes (list[Anime.Episode]): la lista degli episodi da scaricare.
        provider (Provider): il provider da cui scaricare gli episodi.
    """
    async def download_worker(ep: Anime.Episode, task_id: TaskID, progress: Progress, sem: asyncio.Semaphore):
        async with sem:
            filename = path() / anime.name / f"{ep}.mp4"
            if filename.exists():
                progress.update(task_id, completed=100, total=100, description=f"[green]Ep. {ep.num} (Esistente)")
                return

            filename.parent.mkdir(parents=True, exist_ok=True)
            try:
                url = provider.episode_link(anime, ep)
            except Exception as e:
                progress.console.print(f"[red]Errore link Ep. {ep.num}: {e}")
                return

            if streams.is_stream(url):
                await streams.download_stream(url, filename, provider.Client.headers, progress, task_id, ep.num)
                return

            headers = provider.Client.headers
            temp_filename = filename.with_name(f"{filename.name}.temp")
            connections = max(1, ut.config_data["general"].get("connections-per-download", DEFAULT_CONNECTIONS))

            async def single_stream(client: AsyncClient) -> None:
                """Scarica l'episodio con un'unica connessione (fallback)."""
                async with client.stream("GET", url, headers=headers) as response:
                    response.raise_for_status()
                    total = int(response.headers.get('content-length', 0))
                    progress.update(task_id, total=total or None)
                    with open(temp_filename, "wb") as f:
                        async for chunk in response.aiter_bytes(CHUNK_SIZE):
                            if chunk:
                                progress.update(task_id, advance=f.write(chunk))

            async def download_segment(client: AsyncClient, start: int, end: int) -> None:
                """Scarica l'intervallo di byte [start, end] e lo scrive alla sua posizione nel file."""
                seg_headers = {**headers, "Range": f"bytes={start}-{end}"}
                async with client.stream("GET", url, headers=seg_headers) as response:
                    if not _valid_partial_response(response, start, end, total):
                        raise ValueError(
                            f"Risposta Range non valida per bytes={start}-{end}"
                        )
                    with open(temp_filename, "r+b") as f:
                        f.seek(start)
                        async for chunk in response.aiter_bytes(CHUNK_SIZE):
                            if chunk:
                                progress.update(task_id, advance=f.write(chunk))

            try:
                async with AsyncClient(timeout=30.0, follow_redirects=True) as client:
                    total = 0
                    accept_ranges = False
                    try:
                        head = await client.head(url, headers=headers)
                        head.raise_for_status()
                        total = int(head.headers.get('content-length', 0))
                        accept_ranges = head.headers.get('accept-ranges', '').lower() == 'bytes'
                    except Exception:
                        pass

                    if connections > 1 and accept_ranges and total > 0:
                        # Download segmentato: più connessioni in parallelo sullo stesso
                        # file, per aggirare i limiti di banda per-connessione dei CDN.
                        progress.update(task_id, total=total)
                        with open(temp_filename, "wb") as f:
                            f.truncate(total)
                        segments = [
                            download_segment(client, start, end)
                            for start, end in _segment_ranges(total, connections)
                        ]
                        await asyncio.gather(*segments)
                    else:
                        # Server senza supporto ai range (o dimensione ignota): fallback.
                        await single_stream(client)

                temp_filename.rename(filename)
                progress.update(task_id, description=f"[success]Ep. {ep.num} (Completato)[/]")
            except Exception as e:
                progress.console.print(f"[error]Errore download Ep. {ep.num}: {e}[/]")

    async def _download_all():
        concurrent_downloads = ut.config_data["general"].get("parallel-downloads", 3)
        semaphore = asyncio.Semaphore(concurrent_downloads)
        ordered_eps = sorted(episodes, key=lambda e: e.numeric())

        with Progress(
            TextColumn("[info]{task.description}[/]", style="info"),
            BarColumn(bar_width=None),
            "•",
            DownloadColumn(),
            "•",
            TransferSpeedColumn(),
            console=ut.console,
        ) as progress:
            tasks = []
            for ep in ordered_eps:
                task_id = progress.add_task(str(ep), total=None, start=True)
                tasks.append(asyncio.create_task(download_worker(ep, task_id, progress, semaphore)))

            await asyncio.gather(*tasks)

    asyncio.run(_download_all())
