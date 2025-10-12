import pytest
from unittest.mock import MagicMock, mock_open # unittest.mock è nella libreria standard, non è un modulo esterno!
from aw_cli.history import History
from aw_cli.anime import Anime, AnimeStatus

@pytest.fixture(autouse=True)
def mock_utilities(monkeypatch):
    class MockUtilities:
        configData = {
            "general": {
                "specials": True
            }
        }
    monkeypatch.setattr('aw_cli.history.ut', MockUtilities)

# -- Classe Ausiliaria per simulare side_effect --
class MockSequencer:
    """
    Un oggetto 'callable' che restituisce valori/errori diversi
    ad ogni chiamata, imitando il side_effect di un mock.
    """
    def __init__(self, outcomes):
        self._outcomes = outcomes
        self.call_count = 0

    def __call__(self, *args, **kwargs):
        # Questo metodo viene eseguito ogni volta che 'open' viene chiamata
        try:
            result = self._outcomes[self.call_count]
        except IndexError:
            raise AssertionError(f"Chiamata a open() inaspettata (n.{self.call_count + 1})")
        
        self.call_count += 1
        
        if isinstance(result, Exception):
            raise result
        else:
            return result

# volgio testare 3 casi:
# non trovo il file history.json e non esiste aw-cronologia.csv
def test_no_file_found(monkeypatch):
    """
    Testa il caso:
    1. open() -> FileNotFoundError
    2. open() -> FileNotFoundError
    3. open() -> Successo in scrittura
    """
    sequenza = [
        FileNotFoundError("history.json"),
        FileNotFoundError("aw-cronologia.csv"),
        mock_open().return_value
    ]
    mock_sequencer = MockSequencer(sequenza)
    monkeypatch.setattr('builtins.open', mock_sequencer)
    
    history = History()

    assert history._anime_log == []
    assert mock_sequencer.call_count == 3

# non trovo il file history.json ma esiste aw-cronologia.csv
def test_legacy(monkeypatch):
    """
    Testa il caso:
    1. open() -> FileNotFoundError
    2. open() -> Successo in lettura (aw-cronologia.csv)
    3. open() -> Successo in scrittura (history.json)
    """
    mock_handle_scrivibile = mock_open().return_value
    monkeypatch.setattr('builtins.open', lambda *args, **kwargs: mock_handle_scrivibile)
    sequenza = [
        FileNotFoundError("history.json"),
        mock_open(read_data=legacy_data).return_value,
        mock_handle_scrivibile
    ]
    mock_sequencer = MockSequencer(sequenza)
    monkeypatch.setattr('builtins.open', mock_sequencer)

    history = History()

    lista_pezzi_scritti = [call.args[0] for call in mock_handle_scrivibile.write.call_args_list]
    output_completo = "".join(lista_pezzi_scritti)

    assert output_completo == json_data
    assert mock_sequencer.call_count == 3

def test_load_existing(monkeypatch):
    """
    Testa il caso:
    1. open() -> Successo in lettura (history.json)
    """
    sequenza = [
        mock_open(read_data=json_data).return_value,
    ]
    mock_sequencer = MockSequencer(sequenza)
    monkeypatch.setattr('builtins.open', mock_sequencer)

    history = History()
    data = history.get()
    
    assert len(history._anime_log) == 7
    assert data[0].name == "Ore wo Suki nano wa Omae dake ka yo"
    assert data[1].name == "Kaiju No. 8 2"
    assert data[2].name == "Fire Force 3"
    assert data[3].name == "Dan Da Dan 2"
    assert data[4].name == "One Piece"
    assert data[5].name == "Dr. Stone 4 Part 2"
    assert data[6].name == "Sakamoto Days Part 2"
    assert mock_sequencer.call_count == 1

@pytest.fixture
def history_with_data(monkeypatch):
    sequenza = [
        mock_open(read_data=json_data).return_value,
        mock_open().return_value
    ]
    mock_sequencer = MockSequencer(sequenza)
    monkeypatch.setattr('builtins.open', mock_sequencer)

    return History()

def test_remove_anime(history_with_data):
    history = history_with_data
    initial_length = len(history._anime_log)
    
    anime_to_remove = history._anime_log[3]  # Rimuovo "Dan Da Dan 2"
    history.remove(anime_to_remove)
    
    assert len(history._anime_log) == initial_length - 1
    assert all(anime.name != "Dan Da Dan 2" for anime in history._anime_log)

def test_remove_nonexistent_anime(history_with_data):
    history = history_with_data
    initial_length = len(history._anime_log)
    
    fake_anime = MagicMock()
    fake_anime.name = "Nonexistent Anime"
    
    with pytest.raises(ValueError):
        history.remove(fake_anime)
    
    assert len(history._anime_log) == initial_length  # La lunghezza non deve cambiare

# TODO test update con vari casi
# - aggiunta in testa
# - aggiunta in coda 
# - rimozione in caso di anime finito

# TODO test reload

legacy_data  = """Ore wo Suki nano wa Omae dake ka yo,1,1627,12,1,12,104464,1
Kaiju No. 8 2,6,6726,12,0,6,178754,3
Fire Force 3,6,https://www.animeworld.so/play/fire-force-3.dGBJF/tEVpcY,12,1,12,149118,0
Dan Da Dan 2,7,https://www.animeworld.so/play/dan-da-dan-2.IsJ2N,12,0,7,185660,0
One Piece,1140,https://www.animeworld.so/play/one-piece-subita.qzG-LE,??,0,1141,21,0
Dr. Stone 4 Part 2,7,https://www.animeworld.so/play/dr-stone-4-part-2.DeE4h,12,0,7,189117,0
Sakamoto Days Part 2,7,6736,??,0,7,184237,0
"""

json_data = """[
    {
        "name": "Ore wo Suki nano wa Omae dake ka yo",
        "ref": "1627",
        "curr_ep": "1",
        "last_ep": "1",
        "id_anilist": 104464,
        "status": "Finito",
        "info": {
            "Episodi": "12"
        },
        "episodes": [
            {
                "num": "1",
                "ref": "Not available",
                "progress": 1,
                "completed": false
            }
        ]
    },
    {
        "name": "Kaiju No. 8 2",
        "ref": "6726",
        "curr_ep": "6",
        "last_ep": "6",
        "id_anilist": 178754,
        "status": "In corso",
        "info": {
            "Episodi": "12"
        },
        "episodes": [
            {
                "num": "6",
                "ref": "Not available",
                "progress": 3,
                "completed": false
            }
        ]
    },
    {
        "name": "Fire Force 3",
        "ref": "https://www.animeworld.so/play/fire-force-3.dGBJF/tEVpcY",
        "curr_ep": "6",
        "last_ep": "6",
        "id_anilist": 149118,
        "status": "Finito",
        "info": {
            "Episodi": "12"
        },
        "episodes": [
            {
                "num": "6",
                "ref": "Not available",
                "progress": 0,
                "completed": true
            }
        ]
    },
    {
        "name": "Dan Da Dan 2",
        "ref": "https://www.animeworld.so/play/dan-da-dan-2.IsJ2N",
        "curr_ep": "7",
        "last_ep": "7",
        "id_anilist": 185660,
        "status": "In corso",
        "info": {
            "Episodi": "12"
        },
        "episodes": [
            {
                "num": "7",
                "ref": "Not available",
                "progress": 0,
                "completed": true
            }
        ]
    },
    {
        "name": "One Piece",
        "ref": "https://www.animeworld.so/play/one-piece-subita.qzG-LE",
        "curr_ep": "1140",
        "last_ep": "1140",
        "id_anilist": 21,
        "status": "In corso",
        "info": {
            "Episodi": "??"
        },
        "episodes": [
            {
                "num": "1140",
                "ref": "Not available",
                "progress": 0,
                "completed": true
            }
        ]
    },
    {
        "name": "Dr. Stone 4 Part 2",
        "ref": "https://www.animeworld.so/play/dr-stone-4-part-2.DeE4h",
        "curr_ep": "7",
        "last_ep": "7",
        "id_anilist": 189117,
        "status": "In corso",
        "info": {
            "Episodi": "12"
        },
        "episodes": [
            {
                "num": "7",
                "ref": "Not available",
                "progress": 0,
                "completed": true
            }
        ]
    },
    {
        "name": "Sakamoto Days Part 2",
        "ref": "6736",
        "curr_ep": "7",
        "last_ep": "7",
        "id_anilist": 184237,
        "status": "In corso",
        "info": {
            "Episodi": "??"
        },
        "episodes": [
            {
                "num": "7",
                "ref": "Not available",
                "progress": 0,
                "completed": true
            }
        ]
    }
]"""


