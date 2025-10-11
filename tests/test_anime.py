import pytest
from unittest.mock import patch
from aw_cli.anime import Anime

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
"""