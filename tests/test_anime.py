import pytest
from unittest.mock import patch
from awcli.anime import Anime, numeric
import awcli.utilities

@pytest.fixture
def anime():
    return Anime("Test Anime", "test_ref", "5", "10")

def test_episode_comparisons(anime: Anime):
    # Test equality
    ep1 = Anime.Episode(anime, "5", "ref5")
    ep2 = Anime.Episode(anime, "5", "ref5_bis")
    assert ep1 == ep2
    
    # Test less than
    ep3 = Anime.Episode(anime, "3", "ref3")
    ep4 = Anime.Episode(anime, "5", "ref5")
    assert ep3 < ep4
    
    # Test greater than
    ep5 = Anime.Episode(anime, "10", "ref10")
    ep6 = Anime.Episode(anime, "5", "ref5")
    assert ep5 > ep6
    
    # Test less than or equal
    ep7 = Anime.Episode(anime, "5", "ref5")
    ep8 = Anime.Episode(anime, "5", "ref5")
    ep9 = Anime.Episode(anime, "10", "ref10")
    assert ep7 <= ep8
    assert ep7 <= ep9
    
    # Test greater than or equal
    ep10 = Anime.Episode(anime, "10", "ref10")
    ep11 = Anime.Episode(anime, "10", "ref10")
    ep12 = Anime.Episode(anime, "5", "ref5")
    assert ep10 >= ep11
    assert ep10 >= ep12

def test_episode_comparison_with_decimals(anime: Anime):
    ep1 = Anime.Episode(anime, "5", "ref5")
    ep2 = Anime.Episode(anime, "5.5", "ref5.5")
    assert ep1 < ep2

def test_episode_comparison_with_range(anime: Anime):
    ep1 = Anime.Episode(anime, "5-10", "ref5-10")
    ep2 = Anime.Episode(anime, "11", "ref11")
    assert ep1 < ep2

def test_numeric_function():
    assert numeric("5") == 5
    assert numeric("5.5") == 5
    assert numeric("1-5") == 5
    assert numeric("0") == 0

def test_episodes_sorting(anime: Anime):
    episodes = {
        "12": "ref12",
        "5.5": "ref5.5",
        "3-4": "ref3-4",
        "1": "ref1",
        "10": "ref10",
        "0": "ref0",
        "7.5": "ref7.5",
        "2": "ref2",
        "6-7": "ref5-7"
    }
    anime.update_episodes(episodes)
    anime.update_episodes({"5": "ref5"})
    expected = ["0", "1", "2", "3-4", "5", "5.5", "6-7", "7.5", "10", "12"]
    assert anime.episodes() == expected
"""
@pytest.fixture
def anime():
    return awcli.utilities.Anime("Test", "no_url", 20, 26)

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
                "26",
                1,
                232023,
                "trama"
            ]
        )
        yield mock_get_info_anime

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
    assert anime.ep_totali == "26"
    assert anime.status == 1
    assert anime.views == 232023
    assert anime.plot == "trama"
    
def test_load_info_error(anime, mock_get_info_anime):
    mock_get_info_anime.side_effect = IndexError
    with pytest.raises(IndexError):
        anime.load_info()
    assert mock_get_info_anime.call_count == 2


def test_get_episodio(anime, mock_get_info_anime, mock_download):
    anime.load_info()
    for i in range(30):
        anime.get_episodio(i)
    assert mock_download.call_count == anime.ep - anime.ep_ini + 1
"""