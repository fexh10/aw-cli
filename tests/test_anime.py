import pytest
from unittest.mock import patch
import awcli.utilities

@pytest.fixture
def anime():
    return awcli.utilities.Anime("Test", "no_url", 20, 26)

@pytest.fixture
def mock_episodes():
    with patch("awcli.utilities.episodes") as mock_episodes:
        mock_episodes.return_value = (["url1", "url2"], "status", "id_anilist", 2)
        yield mock_episodes
        
@pytest.fixture
def mock_download():
    with patch("awcli.utilities.download") as mock_download:
        mock_download.return_value = "episode_content"
        yield mock_download

def test_load_episodes(anime, mock_episodes):
    anime.load_episodes()
    assert anime.ep == 2
    assert anime.url_episodi == ["url1", "url2"]
    assert anime.status == "status"
    assert anime.id_anilist == "id_anilist"
    assert anime.ep_totali == 2

def test_get_episodio(anime, mock_episodes, mock_download):
    anime.load_episodes()
    for i in range(anime.ep_ini,anime.ep):
        anime.get_episodio(i)
        mock_download.assert_called_once()