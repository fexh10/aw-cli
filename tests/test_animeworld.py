# Importa le dipendenze
from pytest import fixture
from awcli import animeworld
from unittest.mock import patch

# Definisce la fixture mock_get
@fixture
def mock_get():
    with patch('requests.get') as mock:
        yield mock
        


def test_search_onepiece(mock_get):
    with open("search_onepiece") as html:
        mock_get.return_value.text = html.read()

    expected = [
        'One Piece',
        'One Piece (ITA)',
        'One Piece: Episode of Skypiea',
        'One Piece 3D2Y: Superare la Morte di Ace! Rufy e il Giuramento Fatto ai Compagni',
        'One Piece Movie 14: Stampede', 'One Piece: Barto no Himitsu no Heya!',
        'One Piece Movie 15: Red'
    ]
    results = [anime.name for anime in animeworld.search("one piece")]
    
    assert results == expected
        

def test_search_dragonball(mock_get):
    with open("search_dragonball") as html:
        mock_get.return_value.text = html.read()
    results = [anime.name for anime in animeworld.search("dragon ball")]
        
    expected = [
        "Dragon Ball Super",
        "Dragon Ball Kai",
        "Dragon Ball GT (ITA)",
        "Dragon Ball Z (ITA)",
        "Dragon Ball (ITA)",
        "Dragon Ball Super (ITA)",
        "Super Dragon Ball Heroes",
        "Dragon Ball Z: Il Super Saiyan della leggenda",
        "Dragon Ball Super Movie: Broly",
        "Dragon Ball Super Movie: Broly (ITA)",
        "Dragon Ball Super: Super Hero",
        "Dragon Ball Super: Super Hero (ITA)",
    ]
        
    assert results == expected

def test_download(mock_get):
    with open("theeminenceinshadowep13") as html:
        mock_get.return_value.text = html.read()
    results = animeworld.download("https://www.animeworld.tv/play/the-eminence-in-shadow.pzm5j/Dcqo-Q")
    expected = "https://server18.streamingaw.online/DDL/ANIME/KageNoJitsuryokushaNiNaritakute/KageNoJitsuryokushaNiNaritakute_Ep_13_SUB_ITA.mp4"

    assert results == expected

def test_episodes_len(mock_get):
    with open("theeminenceinshadowep13") as html:
        mock_get.return_value.text = html.read()
    
    results = animeworld.episodes("https://www.animeworld.tv/play/the-eminence-in-shadow.pzm5j/Dcqo-Q")

    assert len(results) == 13
    