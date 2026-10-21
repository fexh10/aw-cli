import asyncio
import re
import shutil
from collections import deque
from tempfile import TemporaryDirectory
from time import monotonic
from urllib.parse import urljoin, urlsplit
from pathlib import Path
from httpx import AsyncClient
from rich.filesize import decimal
from rich.progress import Progress, BarColumn, TextColumn, TaskID, DownloadColumn, TransferSpeedColumn, ProgressColumn
from rich.text import Text
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

HLS_CONTENT_TYPES = {"application/vnd.apple.mpegurl", "application/x-mpegurl", "audio/mpegurl", "audio/x-mpegurl"}


def _seconds(clock: str) -> float | None:
    """Converte HH:MM:SS.frazioni (formato ffmpeg) in secondi."""
    match = re.fullmatch(r"(\d+):(\d{2}):(\d{2}(?:\.\d+)?)", clock)
    if not match:
        return None
    return int(match.group(1)) * 3600 + int(match.group(2)) * 60 + float(match.group(3))


def _estimated_size(bytes_done: int, seconds_done: float, total_seconds: float | None) -> int | None:
    if bytes_done <= 0 or seconds_done <= 0 or not total_seconds:
        return None
    return max(bytes_done, round(bytes_done * total_seconds / seconds_done))


class EpisodeAmountColumn(ProgressColumn):
    """Mostra i byte scaricati e una stima del totale HLS quando disponibile."""

    def __init__(self):
        super().__init__()
        self.download_column = DownloadColumn()

    def render(self, task):
        if phase := task.fields.get("phase"):
            return Text(phase)
        if not task.fields.get("hls"):
            return self.download_column.render(task)
        size = decimal(task.fields.get("size", 0))
        if (total := task.fields.get("total_size")) is not None:
            return Text(f"{size} / {decimal(total)}", style="green")
        if estimate := task.fields.get("estimated_size"):
            return Text(f"{size} / ~{decimal(estimate)}", style="green")
        return Text(f"{size} / ? bytes", style="green")


class EpisodeSpeedColumn(ProgressColumn):
    def __init__(self):
        super().__init__()
        self.transfer_column = TransferSpeedColumn()

    def render(self, task):
        if task.fields.get("phase"):
            return Text("")
        if task.fields.get("hls"):
            return Text(task.fields.get("speed", "?"))
        return self.transfer_column.render(task)


def is_hls(url: str, content_type: str = "") -> bool:
    """Riconosce le playlist HLS anche quando l'endpoint non termina in .m3u8."""
    parts = urlsplit(url)
    return (
        parts.path.lower().endswith(".m3u8")
        or (parts.hostname in {"vixcloud.cc", "www.vixcloud.cc"} and parts.path.startswith("/playlist/"))
        or content_type.split(";", 1)[0].strip().lower() in HLS_CONTENT_TYPES
    )


class UnsupportedHLSPlaylist(Exception):
    """La playlist richiede il percorso HLS generale di ffmpeg."""


async def _download_vixcloud_hls(url, client, headers, filename, connections, progress, task_id):
    """Scarica i segmenti TS VixCloud in parallelo e li rimonta con ffmpeg."""
    master = await client.get(url, headers=headers)
    master.raise_for_status()
    if not master.text.lstrip().startswith("#EXTM3U"):
        raise UnsupportedHLSPlaylist("Manifest HLS non valido")

    variants = []
    lines = master.text.splitlines()
    if any(line.startswith("#EXT-X-MEDIA:") for line in lines):
        raise UnsupportedHLSPlaylist("Playlist con tracce separate")
    for index, line in enumerate(lines[:-1]):
        if line.startswith("#EXT-X-STREAM-INF"):
            bandwidth = re.search(r"\bBANDWIDTH=(\d+)", line)
            variant = lines[index + 1].strip()
            if variant and not variant.startswith("#"):
                variants.append((int(bandwidth.group(1)) if bandwidth else 0, variant))

    media = master
    if variants:
        variant_url = urljoin(str(master.url), max(variants)[1])
        media = await client.get(variant_url, headers=headers)
        media.raise_for_status()

    playlist = media.text.splitlines()
    if not playlist or playlist[0].strip() != "#EXTM3U":
        raise UnsupportedHLSPlaylist("Playlist media HLS non valida")
    if "#EXT-X-ENDLIST" not in playlist or any(
        line.startswith(("#EXT-X-MAP", "#EXT-X-BYTERANGE", "#EXT-X-DISCONTINUITY"))
        for line in playlist
    ):
        raise UnsupportedHLSPlaylist("Playlist HLS non compatibile con il download parallelo")

    segment_lines = [(index, line.strip()) for index, line in enumerate(playlist) if line.strip() and not line.startswith("#")]
    if not segment_lines or any(not urlsplit(urljoin(str(media.url), line)).path.lower().endswith(".ts") for _, line in segment_lines):
        raise UnsupportedHLSPlaylist("Segmenti HLS non TS")

    durations = []
    for line in playlist:
        if line.startswith("#EXTINF:"):
            try:
                durations.append(float(line.split(":", 1)[1].split(",", 1)[0]))
            except ValueError as exc:
                raise UnsupportedHLSPlaylist("Durata dei segmenti non valida") from exc
    if len(durations) != len(segment_lines):
        raise UnsupportedHLSPlaylist("Numero di segmenti e durate non corrispondente")

    with TemporaryDirectory(prefix="aw-cli-hls-", dir=filename.parent) as directory:
        workdir = Path(directory)
        local_playlist = playlist.copy()
        for key_index, line in enumerate(playlist):
            if not line.startswith("#EXT-X-KEY"):
                continue
            method = re.search(r"\bMETHOD=([^,]+)", line)
            uri = re.search(r'\bURI="([^"]+)"', line)
            if not method or method.group(1) != "AES-128" or not uri:
                raise UnsupportedHLSPlaylist("Cifratura HLS non supportata")
            key_url = urljoin(str(media.url), uri.group(1))
            key_response = await client.get(key_url, headers=headers)
            key_response.raise_for_status()
            if len(key_response.content) != 16:
                raise ValueError("Chiave AES-128 HLS non valida")
            key_path = workdir / f"key-{key_index}.bin"
            key_path.write_bytes(key_response.content)
            local_playlist[key_index] = line.replace(uri.group(1), key_path.as_uri())

        segments = []
        for segment_index, (line_index, segment) in enumerate(segment_lines):
            target = workdir / f"segment-{segment_index:05d}.ts"
            local_playlist[line_index] = target.as_uri()
            segments.append((urljoin(str(media.url), segment), target, durations[segment_index]))

        total_duration = sum(durations)
        progress.update(task_id, total=total_duration, completed=0, size=0, phase=None)
        semaphore = asyncio.Semaphore(connections)
        started = monotonic()
        downloaded_bytes = 0
        completed_bytes = 0
        completed_duration = 0.0
        estimated_bytes = None

        async def fetch_segment(segment_url, target, duration):
            nonlocal downloaded_bytes, completed_bytes, completed_duration, estimated_bytes
            async with semaphore:
                async with client.stream("GET", segment_url, headers=headers) as response:
                    response.raise_for_status()
                    with target.open("wb") as output:
                        async for chunk in response.aiter_bytes(CHUNK_SIZE):
                            downloaded_bytes += output.write(chunk)
                            elapsed = max(monotonic() - started, 0.001)
                            progress.update(
                                task_id, size=downloaded_bytes,
                                estimated_size=max(downloaded_bytes, estimated_bytes) if estimated_bytes else None,
                                speed=f"{decimal(downloaded_bytes / elapsed)}/s",
                            )
                completed_bytes += target.stat().st_size
                completed_duration += duration
                estimated_bytes = _estimated_size(completed_bytes, completed_duration, total_duration)
                progress.update(task_id, advance=duration, estimated_size=max(downloaded_bytes, estimated_bytes or 0))

        segment_tasks = [asyncio.create_task(fetch_segment(*segment)) for segment in segments]
        try:
            await asyncio.gather(*segment_tasks)
        except BaseException:
            for segment_task in segment_tasks:
                segment_task.cancel()
            await asyncio.gather(*segment_tasks, return_exceptions=True)
            raise
        local_manifest = workdir / "playlist.m3u8"
        local_manifest.write_text("\n".join(local_playlist) + "\n", encoding="utf-8")
        progress.update(task_id, total_size=downloaded_bytes, phase=None,
                        description="[info]Assemblaggio MP4…[/]")
        command = [
            "ffmpeg", "-nostdin", "-loglevel", "error", "-y",
            "-protocol_whitelist", "file,crypto", "-allowed_extensions", "ALL",
            "-i", str(local_manifest), "-c", "copy", "-f", "mp4", str(filename),
        ]
        process = await asyncio.create_subprocess_exec(*command, stderr=asyncio.subprocess.PIPE)
        _, stderr = await process.communicate()
        if process.returncode != 0:
            raise RuntimeError(f"ffmpeg: {stderr.decode(errors='replace').strip()}")
        progress.update(task_id, completed=total_duration, total_size=downloaded_bytes, phase=None)

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
                progress.update(task_id, completed=100, total=100, phase="già presente", description=f"[green]Ep. {ep.num} (Esistente)")
                return

            filename.parent.mkdir(parents=True, exist_ok=True)
            try:
                # Il provider usa richieste HTTP sincrone: non bloccare gli altri episodi.
                url = await asyncio.to_thread(provider.episode_link, anime, ep)
            except Exception as e:
                progress.update(task_id, phase="errore", description=f"[error]Ep. {ep.num} (Errore)[/]")
                progress.stop_task(task_id)
                progress.console.print(f"[red]Errore link Ep. {ep.num}: {e}")
                return
            progress.update(task_id, phase="connessione…")

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
                    content_type = ""
                    known_hls = is_hls(url)
                    if not known_hls:
                        try:
                            head = await client.head(url, headers=headers)
                            head.raise_for_status()
                            total = int(head.headers.get('content-length', 0))
                            accept_ranges = head.headers.get('accept-ranges', '').lower() == 'bytes'
                            content_type = head.headers.get('content-type', '')
                        except Exception:
                            pass

                    if known_hls or is_hls(url, content_type):
                        if shutil.which("ffmpeg") is None:
                            raise RuntimeError("ffmpeg non trovato nel PATH: necessario per scaricare stream HLS")
                        progress.update(task_id, hls=True, size=0, phase="preparazione HLS…")
                        parallel = urlsplit(url).hostname in {"vixcloud.cc", "www.vixcloud.cc"}
                        if parallel:
                            try:
                                await _download_vixcloud_hls(
                                    url, client, headers, temp_filename, connections, progress, task_id
                                )
                            except UnsupportedHLSPlaylist:
                                parallel = False
                        if not parallel:
                            # Altri formati HLS restano gestiti dal demuxer di ffmpeg.
                            command = [
                                "ffmpeg", "-nostdin", "-nostats", "-loglevel", "info",
                                "-stats_period", "0.5", "-progress", "pipe:1", "-y",
                            ]
                            if user_agent := headers.get("User-Agent"):
                                command.extend(["-user_agent", user_agent])
                            command.extend(["-i", url, "-c", "copy", "-f", "mp4", str(temp_filename)])
                            process = await asyncio.create_subprocess_exec(
                                *command, stdout=asyncio.subprocess.PIPE,
                                stderr=asyncio.subprocess.PIPE,
                            )
                            errors = deque(maxlen=12)
                            duration_seconds = None
                            elapsed = 0.0
                            written = 0
                            started = monotonic()

                            async def read_ffmpeg_stderr():
                                nonlocal duration_seconds
                                async for line in process.stderr:
                                    message = line.decode(errors="replace").strip()
                                    errors.append(message)
                                    duration = re.search(r"Duration: (\d+:\d{2}:\d{2}(?:\.\d+)?)", message)
                                    if duration and (duration_seconds := _seconds(duration.group(1))):
                                        progress.update(
                                            task_id, total=duration_seconds, phase=None,
                                            estimated_size=_estimated_size(written, elapsed, duration_seconds),
                                        )

                            stderr_reader = asyncio.create_task(read_ffmpeg_stderr())
                            async for line in process.stdout:
                                key, _, value = line.decode(errors="replace").strip().partition("=")
                                if key == "out_time" and (current := _seconds(value)) is not None:
                                    elapsed = current
                                    progress.update(
                                        task_id, completed=min(elapsed, duration_seconds or elapsed),
                                        estimated_size=_estimated_size(written, elapsed, duration_seconds),
                                    )
                                elif key == "total_size" and value.isdigit():
                                    written = int(value)
                                    progress.update(
                                        task_id, size=written, phase=None,
                                        estimated_size=_estimated_size(written, elapsed, duration_seconds),
                                        speed=f"{decimal(written / max(monotonic() - started, 0.001))}/s",
                                    )
                            await process.wait()
                            await stderr_reader
                            if process.returncode != 0:
                                raise RuntimeError(f"ffmpeg: {'; '.join(errors)}")
                            finished = duration_seconds or elapsed or 1.0
                            final_size = temp_filename.stat().st_size
                            progress.update(task_id, total=finished, completed=finished, size=final_size, total_size=final_size)
                    elif connections > 1 and accept_ranges and total > 0:
                        # Download segmentato: più connessioni in parallelo sullo stesso
                        # file, per aggirare i limiti di banda per-connessione dei CDN.
                        progress.update(task_id, total=total, phase=None)
                        with open(temp_filename, "wb") as f:
                            f.truncate(total)
                        segments = [
                            download_segment(client, start, end)
                            for start, end in _segment_ranges(total, connections)
                        ]
                        await asyncio.gather(*segments)
                    else:
                        # Server senza supporto ai range (o dimensione ignota): fallback.
                        progress.update(task_id, phase=None)
                        await single_stream(client)

                temp_filename.rename(filename)
                progress.update(task_id, description=f"[success]Ep. {ep.num} (Completato)[/]")
            except Exception as e:
                progress.update(task_id, phase="errore", description=f"[error]Ep. {ep.num} (Errore)[/]")
                progress.stop_task(task_id)
                progress.console.print(f"[error]Errore download Ep. {ep.num}: {e}[/]")

    async def _download_all():
        concurrent_downloads = ut.config_data["general"].get("parallel-downloads", 3)
        semaphore = asyncio.Semaphore(concurrent_downloads)
        ordered_eps = sorted(episodes, key=lambda e: e.numeric())

        with Progress(
            TextColumn("[info]{task.description}[/]", style="info"),
            BarColumn(bar_width=None),
            "•",
            EpisodeAmountColumn(),
            "•",
            EpisodeSpeedColumn(),
            console=ut.console,
        ) as progress:
            tasks = []
            for ep in ordered_eps:
                task_id = progress.add_task(str(ep), total=None, start=True, phase="recupero link…")
                tasks.append(asyncio.create_task(download_worker(ep, task_id, progress, semaphore)))

            await asyncio.gather(*tasks)

    asyncio.run(_download_all())
