import asyncio
from pathlib import Path
from httpx import AsyncClient
from rich.progress import Progress, BarColumn, TextColumn, TaskID, DownloadColumn, TransferSpeedColumn
from . import utilities as ut
from .anime import Anime
from .providers import Provider

from functools import lru_cache

# Numero di connessioni parallele usate di default per scaricare un singolo
# episodio. Molti CDN limitano la banda per-connessione: scaricare lo stesso
# file a segmenti con più connessioni aggira quel limite. Sovrascrivibile
# tramite l'opzione "connections-per-download" nel file di configurazione.
DEFAULT_CONNECTIONS = 4

# Dimensione dei blocchi letti dallo stream. 1 MB riduce drasticamente
# l'overhead rispetto a letture da 1 KB su file di centinaia di MB.
CHUNK_SIZE = 1024 * 1024

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

            headers = provider.Client.headers
            temp_filename = filename.with_name(f"{filename.name}.temp")
            connections = max(1, ut.config_data["general"].get("connections-per-download", DEFAULT_CONNECTIONS))

            async def single_stream(client: AsyncClient) -> None:
                """Scarica l'episodio con un'unica connessione (fallback)."""
                async with client.stream("GET", url, headers=headers) as response:
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
                        segment_size = total // connections
                        segments = []
                        for i in range(connections):
                            start = i * segment_size
                            end = total - 1 if i == connections - 1 else start + segment_size - 1
                            segments.append(download_segment(client, start, end))
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
