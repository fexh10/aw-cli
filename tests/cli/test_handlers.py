import sys
sys.argv = ['aw-cli']

import pytest
from unittest.mock import MagicMock, patch
from aw_cli.core.anime import Anime
from aw_cli.cli.handlers import (
    create_ep_menu,
    handle_get_anime_list,
    handle_resolve_episodes,
)

@pytest.fixture
def anime():
    return Anime("Test Anime", "test_ref", "1", "1")

# Parametrized tests for generate_menu (create_ep_menu)
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


# Parametrized tests for handle_get_anime_list
@pytest.mark.parametrize("hist, latest, offline, latest_filter, expected_provider_call, provider_return, expected_res", [
    (False, False, True, None, "search", ["anime_offline"], ["anime_offline"]),
    (False, True, False, "sub", "latest", ["anime_latest"], ["anime_latest"]),
    (True, False, False, None, "history", ["anime_hist"], ["anime_hist"]),
])
def test_handle_get_anime_list(hist, latest, offline, latest_filter, expected_provider_call, provider_return, expected_res):
    provider = MagicMock()
    if expected_provider_call == "search":
        provider.search.return_value = provider_return
    elif expected_provider_call == "latest":
        provider.latest.return_value = provider_return

    with patch("aw_cli.cli.handlers.history") as mock_history:
        if expected_provider_call == "history":
            mock_history.get.return_value = provider_return

        res = handle_get_anime_list(provider, hist=hist, latest=latest, offline=offline, latest_filter=latest_filter)

        if expected_provider_call == "search":
            provider.search.assert_called_once_with("")
        elif expected_provider_call == "latest":
            provider.latest.assert_called_once_with(latest_filter)
        elif expected_provider_call == "history":
            mock_history.get.assert_called_once()

        assert res == expected_res


# Parametrized tests for handle_resolve_episodes
@pytest.mark.parametrize("episodes_list, hist, latest, expected_res, expected_reload", [
    ([], False, False, [], False),
    (["ep1"], False, False, ["ep1"], True),
])
def test_handle_resolve_episodes(episodes_list, hist, latest, expected_res, expected_reload):
    anime = MagicMock()
    anime.episodes.return_value = episodes_list
    anime._episodes = episodes_list
    provider = MagicMock()

    with patch("aw_cli.cli.handlers.console") as mock_console:
        res, reload_list = handle_resolve_episodes(anime, provider, hist=hist, latest=latest, downl=False)
        assert res == expected_res
        assert reload_list == expected_reload


# Tests for CliApp
def test_cliapp_init():
    from aw_cli.run import CliApp
    with patch("aw_cli.run.Fzf") as mock_fzf:
        app = CliApp()
        assert app.provider is None
        assert app.reload is True
        assert app.animelist == []
        mock_fzf.assert_called_once()


def test_cliapp_setup():
    from aw_cli.run import CliApp
    app = CliApp()
    with patch("aw_cli.run.config") as mock_config, \
         patch("aw_cli.run.history") as mock_history, \
         patch("aw_cli.run.create_provider") as mock_create_provider, \
         patch("aw_cli.run.args") as mock_args:

        mock_config.path.exists.return_value = True
        mock_args.start_config = False
        mock_args.action = "search"
        mock_config.data = {"provider": {"source": "animeworld"}}

        app.setup()

        mock_config.load.assert_called_once()
        mock_history.load.assert_called_once()
        mock_create_provider.assert_called_once_with("animeworld")
