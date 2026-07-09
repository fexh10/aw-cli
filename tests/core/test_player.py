import pytest
from unittest.mock import MagicMock
from aw_cli.core import player

@pytest.fixture
def mock_config(monkeypatch):
    config = {
        "player": {
            "path": "mpv",
            "complete_limit": 80
        },
        "syncplay": {
            "path": "syncplay"
        }
    }
    monkeypatch.setattr(player, "config_data", config)
    return config

def test_open_player_android(monkeypatch):
    monkeypatch.setattr(player.env, "os_name", "Android")
    mock_android = MagicMock(return_value=(True, 0))
    monkeypatch.setattr(player, "android_player", mock_android)

    player.open_player("http://example.com/video.mp4", "Test Episode", 100, syncplay=False)
    mock_android.assert_called_once_with("http://example.com/video.mp4", "Test Episode", 100)

def test_open_player_syncplay(monkeypatch, mock_config):
    monkeypatch.setattr(player.env, "os_name", "Linux")
    mock_syncplay = MagicMock(return_value=(True, 0))
    monkeypatch.setattr(player, "open_syncplay", mock_syncplay)

    player.open_player("http://example.com/video.mp4", "Test Episode", 100, syncplay=True)
    mock_syncplay.assert_called_once_with("http://example.com/video.mp4", "Test Episode", 100)

def test_open_player_mpv(monkeypatch, mock_config):
    monkeypatch.setattr(player.env, "os_name", "Linux")
    mock_mpv = MagicMock(return_value=(True, 0))
    monkeypatch.setattr(player, "open_mpv", mock_mpv)

    player.open_player("http://example.com/video.mp4", "Test Episode", 100, syncplay=False)
    mock_mpv.assert_called_once_with("http://example.com/video.mp4", "Test Episode", 100)

def test_android_player(monkeypatch):
    mock_run = MagicMock()
    monkeypatch.setattr("subprocess.run", mock_run)

    completed, progress = player.android_player("http://example.com/video.mp4", "Test Episode", 100)

    assert completed is True
    assert progress == 0
    mock_run.assert_called_once()
    args, kwargs = mock_run.call_args
    assert "org.videolan.vlc" in args[0]
    assert "Test Episode" in args[0]
    assert "http://example.com/video.mp4" in args[0]

def test_open_mpv_linux_success(monkeypatch, mock_config):
    monkeypatch.setattr(player.env, "os_name", "Linux")

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "00:15:30 / 00:20:00 (75%)"

    mock_run = MagicMock(return_value=mock_result)
    monkeypatch.setattr("subprocess.run", mock_run)

    completed, progress = player.open_mpv("http://example.com/video.mp4", "Test Episode", 120)

    # 75% < 80% (complete_limit) -> completed is False
    # 15:30 = 930 seconds
    assert completed is False
    assert progress == 930

    mock_run.assert_called_once_with(
        ["mpv", "http://example.com/video.mp4", "--force-media-title=Test Episode", "--start=120", "--fullscreen", "--keep-open"],
        capture_output=True,
        text=True,
        check=False
    )

def test_open_mpv_linux_complete(monkeypatch, mock_config):
    monkeypatch.setattr(player.env, "os_name", "Linux")

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "00:18:00 / 00:20:00 (90%)"

    mock_run = MagicMock(return_value=mock_result)
    monkeypatch.setattr("subprocess.run", mock_run)

    completed, progress = player.open_mpv("http://example.com/video.mp4", "Test Episode", 120)

    # 90% >= 80% (complete_limit) -> completed is True
    # 18:00 = 1080 seconds
    assert completed is True
    assert progress == 1080

def test_open_mpv_linux_failure(monkeypatch, mock_config):
    monkeypatch.setattr(player.env, "os_name", "Linux")

    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = "Cannot open file / error"

    mock_run = MagicMock(return_value=mock_result)
    monkeypatch.setattr("subprocess.run", mock_run)

    with pytest.raises(RuntimeError) as exc_info:
        player.open_mpv("http://example.com/video.mp4", "Test Episode", 120)

    assert "Impossibile leggere l'output di MPV" in str(exc_info.value)

def test_open_syncplay_success(monkeypatch, mock_config):
    monkeypatch.setattr(player.env, "os_name", "Linux")

    mock_result = MagicMock()
    mock_result.returncode = 0
    # Simuliamo un output in cui la durata è 1200 e la posizione è 960 (80%)
    mock_result.stdout = "MediaPlayer: player duration: 1200\nMediaPlayer: player position: 960"
    mock_result.stderr = ""

    mock_run = MagicMock(return_value=mock_result)
    monkeypatch.setattr("subprocess.run", mock_run)

    completed, progress = player.open_syncplay("http://example.com/video.mp4", "Test Episode", 120)

    # 960 * 100 // 1200 = 80 >= 80 (complete_limit) -> completed is True
    assert completed is True
    assert progress == 960

    mock_run.assert_called_once()
    args, kwargs = mock_run.call_args
    assert "syncplay" in args[0]
    assert "--force-media-title=\"Test Episode\"" in args[0]

def test_open_syncplay_failure(monkeypatch, mock_config):
    monkeypatch.setattr(player.env, "os_name", "Linux")

    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = "Connection error / syncplay failed to launch"
    mock_result.stderr = ""

    mock_run = MagicMock(return_value=mock_result)
    monkeypatch.setattr("subprocess.run", mock_run)

    with pytest.raises(RuntimeError) as exc_info:
        player.open_syncplay("http://example.com/video.mp4", "Test Episode", 120)

    assert "Impossibile leggere l'output di Syncplay!" in str(exc_info.value)
