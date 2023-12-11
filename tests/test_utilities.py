# Importa le dipendenze
import pytest
import os
from awcli import utilities
from unittest.mock import patch

TEST_DIR = os.path.dirname(os.path.abspath(__file__))

# Definisce la fixture mock_get
@pytest.fixture
def mock_get():
    with patch('requests.get') as mock:
        mock.return_value.status_code = 200
        yield mock

@pytest.mark.parametrize("input,expected", [
    ("search_onepiece", ['One Piece','One Piece (ITA)','One Piece: Episode of Skypiea','One Piece 3D2Y: Superare la Morte di Ace! Rufy e il Giuramento Fatto ai Compagni','One Piece Movie 14: Stampede', 'One Piece: Barto no Himitsu no Heya!','One Piece Movie 15: Red']),
    ("search_dragonball", ["Dragon Ball Super","Dragon Ball Kai","Dragon Ball GT (ITA)","Dragon Ball Z (ITA)","Dragon Ball (ITA)","Dragon Ball Super (ITA)","Super Dragon Ball Heroes","Dragon Ball Z: Il Super Saiyan della leggenda","Dragon Ball Super Movie: Broly","Dragon Ball Super Movie: Broly (ITA)","Dragon Ball Super: Super Hero","Dragon Ball Super: Super Hero (ITA)",]),
    ("empty", []),
])
def test_search(mock_get, input, expected):
    input = TEST_DIR + "/" + input
    with open(input, 'r') as html:
        mock_get.return_value.text = html.read()

    results = [anime.name for anime in utilities.search(input)]
    assert results == expected

def test_download(mock_get):
    input = TEST_DIR + "/" + "theeminenceinshadowep13"
    with open(input) as html:
        mock_get.return_value.text = html.read()
    
    results = utilities.download(input)
    expected = "https://server18.streamingaw.online/DDL/ANIME/KageNoJitsuryokushaNiNaritakute/KageNoJitsuryokushaNiNaritakute_Ep_13_SUB_ITA.mp4"
    ##assert results == expected
    
def test_get_info_anime(mock_get):
    input = TEST_DIR + "/" + "theeminenceinshadowep13"
    with open(input) as html:
        mock_get.return_value.text = html.read()
    
    results = utilities.get_info_anime(input)
    expected = [
        "Anime",
        "Giapponese",
        "05 Ottobre 2022",
        "Autunno 2022",
        "Nexus",
        "Arti Marziali, Avventura, Azione, Commedia, Fantasy, Harem, Scolastico",
        "8.47 / 10",
        "23 min/ep",
        "20",
        "1",
        "1.387.659",
        "Gli uomini che vivono nell'ombra sono quelle persone che passano inosservate, come persone ordinarie, ma in realtà detengono il potere da dietro le quinte. Questo è ciò a cui aspira Shido e per raggiungere il suo obiettivo vive una vita insignificante di giorno, mentre di notte si allena duramente preparandosi alla sua ascesa al potere. Finalmente riesce a raggiungere il suo obiettivo quando, dopo un fatale incidente, si risveglia in un mondo misterioso e si ritrova a capo di un'organizzazione segreta che combatte i demoni rimanendo nell'oscurità!"
    ]
    assert results[0] == 130298
    assert len(results[1]) == 20
    assert results[2] == expected

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

