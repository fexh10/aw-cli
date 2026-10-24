from pathlib import Path
from aw_cli import utilities as ut
from aw_cli import download


def test_sanitize_filename_blocks_traversal_and_invalid_chars(monkeypatch):
    monkeypatch.setattr(ut, "os_name", "Windows")
    assert ".." not in ut.sanitize_filename("../../Windows/System32")
    assert ":" not in ut.sanitize_filename("Le Bizzarre Avventure di JoJo: Stardust")
    assert not ut.sanitize_filename("Bakuman... ").endswith(".")
    assert "\x00" not in ut.sanitize_filename("Test\x00Anime")


def test_download_path_supports_secondary_drive_config(tmp_path, monkeypatch):
    secondary_drive_dir = tmp_path / "SecondaryDrive" / "Anime"
    monkeypatch.setitem(ut.config_data, "general", {"download-path": str(secondary_drive_dir)})
    resolved = download.path(create=True)
    assert resolved == secondary_drive_dir
    assert resolved.exists()


def test_data_dir_respects_aw_cli_home_env(tmp_path, monkeypatch):
    custom_home = tmp_path / "CustomDataHome"
    monkeypatch.setenv("AW_CLI_HOME", str(custom_home))
    resolved = ut.get_data_dir()
    assert resolved == custom_home
    assert resolved.exists()
