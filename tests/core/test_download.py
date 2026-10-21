import asyncio
from types import SimpleNamespace
import httpx
from rich.progress import Progress

from aw_cli import download, download_hls as hls


def response(status_code: int, content_range: str = ""):
    return SimpleNamespace(
        status_code=status_code,
        headers={"content-range": content_range} if content_range else {},
    )


def test_segment_ranges_cover_file_without_gaps():
    assert download._segment_ranges(total=10, connections=3) == [
        (0, 3),
        (4, 6),
        (7, 9),
    ]


def test_segment_ranges_do_not_create_empty_ranges():
    assert download._segment_ranges(total=3, connections=10) == [
        (0, 0),
        (1, 1),
        (2, 2),
    ]


def test_valid_partial_response_accepts_matching_content_range():
    assert download._valid_partial_response(
        response(206, "bytes 4-6/10"),
        start=4,
        end=6,
        total=10,
    )


def test_valid_partial_response_rejects_ignored_range():
    assert not download._valid_partial_response(
        response(200, "bytes 0-9/10"),
        start=4,
        end=6,
        total=10,
    )


def test_valid_partial_response_rejects_wrong_content_range():
    assert not download._valid_partial_response(
        response(206, "bytes 0-6/10"),
        start=4,
        end=6,
        total=10,
    )


def test_is_hls_recognizes_vixcloud_playlist_without_extension():
    assert hls.is_hls("https://vixcloud.cc/playlist/987?token=x&expires=123")
    assert hls.is_hls("https://cdn.example.org/master.m3u8?token=x")
    assert hls.is_hls("https://cdn.example.org/video", "application/vnd.apple.mpegurl; charset=utf-8")
    assert not hls.is_hls("https://cdn.example.org/video.mp4")


def test_hls_progress_shows_green_bytes_and_estimated_total():
    assert hls.seconds("00:01:30.50") == 90.5
    assert hls.estimated_size(1_200_000, 90, 120) == 1_600_000
    with Progress() as progress:
        task_id = progress.add_task("Ep. 1", total=None, hls=True, phase="preparazione HLS…")
        column = hls.EpisodeAmountColumn()
        task = progress.tasks[task_id]
        assert column.render(task).plain == "preparazione HLS…"

        progress.update(task_id, total=120, completed=90.5, size=1_200_000,
                        estimated_size=1_600_000, speed="1.5 MB/s", phase=None)
        display = column.render(task)
        assert display.plain == "1.2 MB / ~1.6 MB"
        assert display.style == "green"
        assert hls.EpisodeSpeedColumn().render(task).plain == "1.5 MB/s"

        progress.update(task_id, size=1_650_000, total_size=1_650_000)
        assert column.render(task).plain == "1.6 MB / 1.6 MB"


def test_vixcloud_hls_downloads_segments_in_parallel(tmp_path, monkeypatch):
    media = "\n".join([
        "#EXTM3U", "#EXT-X-VERSION:3", "#EXT-X-TARGETDURATION:8",
        '#EXT-X-KEY:METHOD=AES-128,URI="key",IV=0x00000000000000000000000000000001',
        *(line for index in range(4) for line in ("#EXTINF:8,", f"seg/{index}.ts")),
        "#EXT-X-ENDLIST", "",
    ])
    active = 0
    maximum = 0

    async def handler(request):
        nonlocal active, maximum
        if request.url.path == "/playlist/1":
            return httpx.Response(200, text="#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=1000\n/variant.m3u8\n")
        if request.url.path == "/variant.m3u8":
            return httpx.Response(200, text=media)
        if request.url.path == "/key":
            return httpx.Response(200, content=b"k" * 16)
        if not request.url.path.startswith("/seg/"):
            raise AssertionError(f"Richiesta HTTP inattesa nel test offline: {request.url}")
        active += 1
        maximum = max(maximum, active)
        await asyncio.sleep(0.01)
        active -= 1
        return httpx.Response(200, content=request.url.path.encode())

    class FakeProcess:
        returncode = 0

        async def communicate(self):
            return b"", b""

    async def fake_ffmpeg(*command, **kwargs):
        manifest = command[command.index("-i") + 1]
        assert "file://" in open(manifest, encoding="utf-8").read()
        for index in range(4):
            assert (next(tmp_path.glob("aw-cli-hls-*/")) / f"segment-{index:05d}.ts").read_bytes() == f"/seg/{index}.ts".encode()
        (tmp_path / "episode.mp4.temp").write_bytes(b"mp4")
        return FakeProcess()

    monkeypatch.setattr(hls.asyncio, "create_subprocess_exec", fake_ffmpeg)

    async def run():
        # MockTransport gestisce tutte le richieste in memoria: il test non usa
        # DNS, socket o una connessione a Internet.
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            progress = Progress(disable=True)
            task_id = progress.add_task("Ep. 1", total=None, hls=True)
            await hls.download_vixcloud(
                "https://vixcloud.cc/playlist/1", client, {},
                tmp_path / "episode.mp4.temp", 4, progress, task_id,
            )
            assert progress.tasks[task_id].completed == 32

    asyncio.run(run())
    assert maximum == 4
    assert (tmp_path / "episode.mp4.temp").read_bytes() == b"mp4"
