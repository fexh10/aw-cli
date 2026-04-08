import sys
sys.argv = ['aw-cli']

import pytest
from aw_cli.anime import Anime
from aw_cli.run import create_ep_menu

@pytest.fixture
def anime():
    return Anime("Test Anime", "test_ref", "1", "1")

# Parametrized tests for generate_menu
@pytest.mark.parametrize("has_next, has_prev, eps_count, last_ep, expected_menu_items", [
    (False, False, 1, "1", ["esci", "indietro", "riguarda"]),
    (True, False, 2, "2", ["esci", "indietro", "seleziona", "riguarda", "prossimo"]),
    (False, True, 2, "2", ["esci", "indietro", "seleziona", "antecedente", "riguarda"]),
    (True, True, 3, "3", ["esci", "indietro", "seleziona", "antecedente", "riguarda", "prossimo"]),
    # Test 'seleziona' logic
    (False, False, 1, "2", ["esci", "indietro", "seleziona", "riguarda"]), # last_ep != '1'
    (False, False, 2, "1", ["esci", "indietro", "seleziona", "riguarda"]), # len(eps) > 1
    (False, False, 1, "1", ["esci", "indietro", "riguarda"]),
])
def test_generate_menu(anime, monkeypatch, has_next, has_prev, eps_count, last_ep, expected_menu_items):
    anime.last_ep = last_ep

    monkeypatch.setattr(anime, 'episodes', lambda: ["1"] * eps_count)

    episode = Anime.Episode(anime, "1", "ref")
    monkeypatch.setattr(episode, 'has_next', lambda: has_next)
    monkeypatch.setattr(episode, 'has_prev', lambda: has_prev)

    menu = create_ep_menu(anime, episode)

    assert list(menu.keys()) == expected_menu_items
