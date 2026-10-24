"""Download e assemblaggio degli stream HLS."""

import asyncio
import re
from collections import deque
from pathlib import Path
from tempfile import TemporaryDirectory
from time import monotonic
from urllib.parse import urljoin, urlsplit

from httpx import AsyncClient
from rich.filesize import decimal
from rich.progress import DownloadColumn, Progress, ProgressColumn, TaskID, TransferSpeedColumn
from rich.text import Text
from . import utilities as ut

CHUNK_SIZE = 1024 * 1024
HLS_CONTENT_TYPES = {
    "application/vnd.apple.mpegurl",
    "application/x-mpegurl",
    "audio/mpegurl",
    "audio/x-mpegurl",
}


def seconds(clock: str) -> float | None:
    """Converte HH:MM:SS.frazioni (formato ffmpeg) in secondi."""
    match = re.fullmatch(r"(\d+):(\d{2}):(\d{2}(?:\.\d+)?)", clock)
    if not match:
        return None
    return int(match.group(1)) * 3600 + int(match.group(2)) * 60 + float(match.group(3))


def estimated_size(bytes_done: int, seconds_done: float, total_seconds: float | None) -> int | None:
    if bytes_done <= 0 or seconds_done <= 0 or not total_seconds:
        return None
    return max(bytes_done, round(bytes_done * total_seconds / seconds_done))


class EpisodeAmountColumn(ProgressColumn):
    """Mostra byte esatti per HTTP e una stima del totale per HLS."""

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


async def download_vixcloud(
    url: str,
    client: AsyncClient,
    headers,
    filename: Path,
    connections: int,
    progress: Progress,
    task_id: TaskID,
) -> None:
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
        media = await client.get(urljoin(str(master.url), max(variants)[1]), headers=headers)
        media.raise_for_status()

    playlist = media.text.splitlines()
    if not playlist or playlist[0].strip() != "#EXTM3U":
        raise UnsupportedHLSPlaylist("Playlist media HLS non valida")
    if "#EXT-X-ENDLIST" not in playlist or any(
        line.startswith(("#EXT-X-MAP", "#EXT-X-BYTERANGE", "#EXT-X-DISCONTINUITY"))
        for line in playlist
    ):
        raise UnsupportedHLSPlaylist("Playlist HLS non compatibile con il download parallelo")

    segment_lines = [
        (index, line.strip())
        for index, line in enumerate(playlist)
        if line.strip() and not line.startswith("#")
    ]
    if not segment_lines or any(
        not urlsplit(urljoin(str(media.url), line)).path.lower().endswith(".ts")
        for _, line in segment_lines
    ):
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
            key_response = await client.get(urljoin(str(media.url), uri.group(1)), headers=headers)
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
                                task_id,
                                size=downloaded_bytes,
                                estimated_size=max(downloaded_bytes, estimated_bytes) if estimated_bytes else None,
                                speed=f"{decimal(downloaded_bytes / elapsed)}/s",
                            )
                completed_bytes += target.stat().st_size
                completed_duration += duration
                estimated_bytes = estimated_size(completed_bytes, completed_duration, total_duration)
                progress.update(
                    task_id,
                    advance=duration,
                    estimated_size=max(downloaded_bytes, estimated_bytes or 0),
                )

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
        progress.update(
            task_id,
            total_size=downloaded_bytes,
            phase=None,
            description="[info]Assemblaggio MP4…[/]",
        )
        ffmpeg_bin = ut.find_binary("ffmpeg") or "ffmpeg"
        command = [
            ffmpeg_bin, "-nostdin", "-loglevel", "error", "-y",
            "-protocol_whitelist", "file,crypto", "-allowed_extensions", "ALL",
            "-i", str(local_manifest), "-c", "copy", "-f", "mp4", str(filename),
        ]
        process = await asyncio.create_subprocess_exec(*command, stderr=asyncio.subprocess.PIPE)
        _, stderr = await process.communicate()
        if process.returncode != 0:
            raise RuntimeError(f"ffmpeg: {stderr.decode(errors='replace').strip()}")
        progress.update(task_id, completed=total_duration, total_size=downloaded_bytes, phase=None)


async def download_with_ffmpeg(
    url: str,
    headers,
    filename: Path,
    progress: Progress,
    task_id: TaskID,
) -> None:
    """Gestisce con ffmpeg le playlist HLS non supportate dal percorso parallelo."""
    ffmpeg_bin = ut.find_binary("ffmpeg") or "ffmpeg"
    command = [
        ffmpeg_bin, "-nostdin", "-nostats", "-loglevel", "info",
        "-stats_period", "0.5", "-progress", "pipe:1", "-y",
    ]
    if user_agent := headers.get("User-Agent"):
        command.extend(["-user_agent", user_agent])
    command.extend(["-i", url, "-c", "copy", "-f", "mp4", str(filename)])
    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    assert process.stdout is not None
    assert process.stderr is not None
    stdout = process.stdout
    stderr = process.stderr
    errors = deque(maxlen=12)
    duration_seconds = None
    elapsed = 0.0
    written = 0
    started = monotonic()

    async def read_stderr():
        nonlocal duration_seconds
        async for line in stderr:
            message = line.decode(errors="replace").strip()
            errors.append(message)
            duration = re.search(r"Duration: (\d+:\d{2}:\d{2}(?:\.\d+)?)", message)
            if duration and (duration_seconds := seconds(duration.group(1))):
                progress.update(
                    task_id,
                    total=duration_seconds,
                    phase=None,
                    estimated_size=estimated_size(written, elapsed, duration_seconds),
                )

    stderr_reader = asyncio.create_task(read_stderr())
    async for line in stdout:
        key, _, value = line.decode(errors="replace").strip().partition("=")
        if key == "out_time" and (current := seconds(value)) is not None:
            elapsed = current
            progress.update(
                task_id,
                completed=min(elapsed, duration_seconds or elapsed),
                estimated_size=estimated_size(written, elapsed, duration_seconds),
            )
        elif key == "total_size" and value.isdigit():
            written = int(value)
            progress.update(
                task_id,
                size=written,
                phase=None,
                estimated_size=estimated_size(written, elapsed, duration_seconds),
                speed=f"{decimal(round(written / max(monotonic() - started, 0.001)))}/s",
            )
    await process.wait()
    await stderr_reader
    if process.returncode != 0:
        raise RuntimeError(f"ffmpeg: {'; '.join(errors)}")
    finished = duration_seconds or elapsed or 1.0
    final_size = filename.stat().st_size
    progress.update(
        task_id,
        total=finished,
        completed=finished,
        size=final_size,
        total_size=final_size,
    )
