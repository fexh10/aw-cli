# Importa le dipendenze
import pytest
from awcli import utilities
from unittest.mock import patch

# Definisce la fixture mock_get
@pytest.fixture
def mock_get():
    with patch('requests.get') as mock:
        yield mock

@pytest.mark.parametrize("input,expected", [
    ("search_onepiece", ['One Piece','One Piece (ITA)','One Piece: Episode of Skypiea','One Piece 3D2Y: Superare la Morte di Ace! Rufy e il Giuramento Fatto ai Compagni','One Piece Movie 14: Stampede', 'One Piece: Barto no Himitsu no Heya!','One Piece Movie 15: Red']),
    ("search_dragonball", ["Dragon Ball Super","Dragon Ball Kai","Dragon Ball GT (ITA)","Dragon Ball Z (ITA)","Dragon Ball (ITA)","Dragon Ball Super (ITA)","Super Dragon Ball Heroes","Dragon Ball Z: Il Super Saiyan della leggenda","Dragon Ball Super Movie: Broly","Dragon Ball Super Movie: Broly (ITA)","Dragon Ball Super: Super Hero","Dragon Ball Super: Super Hero (ITA)",]),
    ("empty", []),
])
def test_search(mock_get, input, expected):
    with open(input, 'r') as html:
        mock_get.return_value.text = html.read()

    results = [anime.name for anime in utilities.search(input)]
    assert results == expected

def test_download(mock_get):
    with open("theeminenceinshadowep13") as html:
        mock_get.return_value.text = html.read()
    
    results = utilities.download("theeminenceinshadowep13")
    expected = "https://server18.streamingaw.online/DDL/ANIME/KageNoJitsuryokushaNiNaritakute/KageNoJitsuryokushaNiNaritakute_Ep_13_SUB_ITA.mp4"
    assert results == expected

def test_episodes_len(mock_get):
    with open("theeminenceinshadowep13") as html:
        mock_get.return_value.text = html.read()
    
    results = utilities.episodes("theeminenceinshadowep13")
    assert len(results) == 13
        
def test_get_episodio(mock_get):
    with open("theeminenceinshadowep13") as html:
        mock_get.return_value.text = html.read()

    anime = utilities.Anime("test", "theeminenceinshadowep13")
    anime.load_episodes()
    expected = "https://server18.streamingaw.online/DDL/ANIME/KageNoJitsuryokushaNiNaritakute/KageNoJitsuryokushaNiNaritakute_Ep_13_SUB_ITA.mp4"
    assert anime.get_episodio(13) == expected

@pytest.mark.parametrize("input_str, format_func, input_values, expected_output", [
    ("Inserisci un numero", lambda i: int(i) if i.isdigit() else None, ["abc", "5"], 5),
    ("Inserisci una stringa", lambda i: i if i else None, ["", "hello"], "hello"),
    ("Inserisci un numero", lambda i: int(i) if i.isdigit() else None, ["abc", "10"], 10),
])
@patch("builtins.input")
def test_my_input(input_mock, input_str, format_func, input_values, expected_output):
    # Mock della funzione di input
    input_mock.side_effect = input_values
    # Esegue il test
    result = utilities.my_input(input_str, format_func)
    # Verifica che il risultato sia corretto
    assert result == expected_output

