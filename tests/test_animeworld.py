# Importa le dipendenze
from pytest import fixture
from awcli.animeworld import AnimeWorld
from unittest.mock import patch

# Definisce la fixture anime_world
@fixture
def anime_world():
    return AnimeWorld()

@fixture
def mock_get():
    with patch('requests.get') as mock:
        yield mock
        

# Definisce la prima funzione di test
def test_search_onepiece(anime_world, mock_get):
    with open("search_onepiece.html") as html:
        mock_get.return_value.text = html.read()

    expected = [
        'One Piece',
        'One Piece (ITA)',
        'One Piece: Episode of Skypiea',
        'One Piece 3D2Y: Superare la Morte di Ace! Rufy e il Giuramento Fatto ai Compagni',
        'One Piece Movie 14: Stampede', 'One Piece: Barto no Himitsu no Heya!',
        'One Piece Movie 15: Red'
    ]

    results = [anime.name for anime in anime_world.search("one piece")]
        
    assert results == expected
        

def test_search_dragonball(anime_world, mock_get):
    with open("search_dragonball.html") as html:
        mock_get.return_value.text = html.read()
    results = [anime.name for anime in anime_world.search("dragon ball")]
        
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

    results = [anime.name for anime in anime_world.search("one piece")]
        
    assert results == expected