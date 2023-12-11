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
        
@pytest.fixture
def mock_get_info_anime():
    with patch("awcli.utilities.get_info_anime") as mock_get_info_anime:
        mock_get_info_anime.return_value = (
            23,
            ["url1", "url2", "url3", "url4", "url5", "url6", "url7", "url8", "url9", "url10", "url11", "url12", "url13", "url14", "url15", "url16", "url17", "url18", "url19", "url20"],
            [
                "categoria", 
                "lingua", 
                "data", 
                "stagione", 
                "studio", 
                "genere", 
                "voto", 
                "durata", 
                26, 
                "stato", 
                232023, 
                "trama"
            ]
        )
        yield mock_get_info_anime        

def test_load_episodes(anime, mock_episodes):
    anime.load_episodes()
    assert anime.ep == 2
    assert anime.url_episodi == ["url1", "url2"]
    assert anime.status == "status"
    assert anime.id_anilist == "id_anilist"
    assert anime.ep_totali == 2
    
def test_load_info(anime, mock_get_info_anime):
    anime.load_info()
    assert anime.id_anilist == 23
    assert anime.ep == 20
    assert anime.category == "categoria"
    assert anime.audio == "lingua"
    assert anime.release_date == "data"
    assert anime.season == "stagione"
    assert anime.studios == "studio"
    assert anime.genres == "genere"
    assert anime.ep_len == "durata"
    assert anime.ep_totali == 26
    assert anime.status == "stato"
    assert anime.views == 232023
    assert anime.plot == "trama"


def test_get_episodio(anime, mock_episodes, mock_download):
    anime.load_episodes()
    for i in range(anime.ep_ini,anime.ep):
        anime.get_episodio(i)
        mock_download.assert_called_once()