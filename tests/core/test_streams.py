import asyncio
import pytest
from pathlib import Path
from unittest.mock import MagicMock
from httpx import Headers
from aw_cli import streams

MASTER = """#EXTM3U
#EXT-X-VERSION:3
#EXT-X-STREAM-INF:BANDWIDTH=1400000,RESOLUTION=854x480
./480p/playlist_480p.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=500000,RESOLUTION=426x240
./240p/playlist_240p.m3u8
"""

VARIANT = """#EXTM3U
#EXT-X-TARGETDURATION:10
#EXTINF:10.0,
480p-000.ts
#EXTINF:10.0,
480p-001.ts
#EXTINF:4.5,
480p-002.ts
#EXT-X-ENDLIST
"""


class FakeClient:
    """Client HTTP asincrono finto che restituisce testi prefissati in base all'URL."""

    def __init__(self, pages: dict[str, str]):
        self.pages = pages
        self.requested: list[str] = []

    async def get(self, url: str):
        self.requested.append(url)
        response = MagicMock()
        response.text = self.pages[url]
        return response


class FakeProcess:
    """Processo ffmpeg finto: emette le righe di -progress e termina con il codice indicato."""

    def __init__(self, lines: list[str], returncode: int = 0, stderr: bytes = b""):
        self.stdout = self._stream(lines)
        self.returncode = returncode
        self._stderr = stderr

    @staticmethod
    async def _stream(lines: list[str]):
        for line in lines:
            yield f"{line}\n".encode()

    async def communicate(self):
        return b"", self._stderr


@pytest.mark.parametrize(
    "url, expected",
    [
        ("https://srv17.example.org/_t/1/abc/DDL/ANIME/Naruto/001/playlist.m3u8", True),
        ("https://srv17.example.org/playlist.m3u8?token=abc", True),
        ("https://srv23.example.org/DDL/ANIME/Naruto/Naruto_Ep_001_SUB_ITA.mp4", False),
        ("https://www.youtube.com/watch?v=abc", False),
    ],
)
def test_is_hls(url, expected):
    assert streams.is_hls(url) is expected


@pytest.mark.parametrize(
    "url, expected",
    [
        ("https://www.youtube.com/watch?v=abc", True),
        ("https://youtu.be/abc", True),
        ("https://srv17.example.org/playlist.m3u8", True),
        ("https://srv23.example.org/DDL/ANIME/Naruto/Naruto_Ep_001_SUB_ITA.mp4", False),
    ],
)
def test_is_stream(url, expected):
    assert streams.is_stream(url) is expected


def test_hls_duration_master_playlist():
    base = "https://srv.example.org/DDL/ANIME/Naruto/001/"
    client = FakeClient({
        base + "playlist.m3u8": MASTER,
        base + "480p/playlist_480p.m3u8": VARIANT,
    })

    duration = asyncio.run(streams.hls_duration(client, base + "playlist.m3u8"))  # type: ignore[arg-type]
    assert duration == pytest.approx(24.5)
    # deve scegliere la variante con la qualità più alta
    assert client.requested[-1] == base + "480p/playlist_480p.m3u8"


def test_hls_duration_media_playlist():
    url = "https://srv.example.org/480p/playlist_480p.m3u8"
    client = FakeClient({url: VARIANT})
    assert asyncio.run(streams.hls_duration(client, url)) == pytest.approx(24.5)  # type: ignore[arg-type]


def test_download_hls_without_ffmpeg(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(streams.shutil, "which", lambda _: None)
    with pytest.raises(RuntimeError, match="ffmpeg"):
        asyncio.run(streams.download_hls(
            "https://srv.example.org/playlist.m3u8", tmp_path / "ep.mp4.temp", Headers(), MagicMock(), MagicMock()
        ))


def test_download_hls_runs_ffmpeg(monkeypatch, tmp_path: Path):
    calls = []

    async def fake_exec(*args, **kwargs):
        calls.append(args)
        return FakeProcess([
            "total_size=1000", "out_time_us=5000000", "progress=continue",
            "total_size=4900", "out_time_us=24500000", "progress=end",
        ])

    async def fake_duration(client, url):
        return 24.5

    monkeypatch.setattr(streams.shutil, "which", lambda _: "/usr/bin/ffmpeg")
    monkeypatch.setattr(streams.asyncio, "create_subprocess_exec", fake_exec)
    monkeypatch.setattr(streams, "hls_duration", fake_duration)

    url = "https://srv.example.org/playlist.m3u8"
    output = tmp_path / "ep.mp4.temp"
    progress = MagicMock()
    asyncio.run(streams.download_hls(url, output, Headers({"User-Agent": "UA-test"}), progress, MagicMock()))

    args = calls[0]
    assert args[0] == "/usr/bin/ffmpeg"
    assert args[args.index("-i") + 1] == url
    assert args[args.index("-user_agent") + 1] == "UA-test"
    assert args[args.index("-c") + 1] == "copy"
    # l'output ha estensione .temp, quindi il formato va indicato esplicitamente
    assert args[args.index("-f") + 1] == "mp4"
    assert args[-1] == str(output)

    # prima stima: 1000 byte per 5 s su 24.5 s totali
    first = progress.update.call_args_list[0].kwargs
    assert first["completed"] == 1000
    assert first["total"] == pytest.approx(4900)
    # alla fine la barra è completa
    assert progress.update.call_args_list[-1].kwargs == {"completed": 4900, "total": 4900}


def test_download_hls_ffmpeg_error(monkeypatch, tmp_path: Path):
    async def fake_exec(*args, **kwargs):
        return FakeProcess([], returncode=1, stderr=b"https://x/playlist.m3u8: Server returned 403 Forbidden\n")

    async def fake_duration(client, url):
        raise ConnectionError("rete non disponibile")

    monkeypatch.setattr(streams.shutil, "which", lambda _: "/usr/bin/ffmpeg")
    monkeypatch.setattr(streams.asyncio, "create_subprocess_exec", fake_exec)
    monkeypatch.setattr(streams, "hls_duration", fake_duration)

    output = tmp_path / "ep.mp4.temp"
    output.write_bytes(b"parziale")
    with pytest.raises(RuntimeError, match="403 Forbidden"):
        asyncio.run(streams.download_hls(
            "https://x/playlist.m3u8", output, Headers(), MagicMock(), MagicMock()
        ))
    assert not output.exists(), "Il file parziale deve essere eliminato in caso di errore"



def test_download_stream_success(monkeypatch, tmp_path: Path):
    async def fake_download_hls(url, output, headers, progress, task_id):
        output.write_bytes(b"video")

    monkeypatch.setattr(streams, "download_hls", fake_download_hls)

    filename = tmp_path / "Naruto Ep. 1.mp4"
    progress = MagicMock()
    asyncio.run(streams.download_stream(
        "https://srv.example.org/playlist.m3u8", filename, Headers(), progress, MagicMock(), "1"
    ))
    assert filename.read_bytes() == b"video"
    assert not filename.with_name(f"{filename.name}.temp").exists()
    assert "Completato" in progress.update.call_args.kwargs["description"]


def test_download_stream_youtube(tmp_path: Path):
    filename = tmp_path / "Naruto Ep. 1.mp4"
    progress = MagicMock()
    asyncio.run(streams.download_stream(
        "https://www.youtube.com/watch?v=abc", filename, Headers(), progress, MagicMock(), "1"
    ))
    assert not filename.exists()
    assert "YouTube" in progress.console.print.call_args.args[0]
