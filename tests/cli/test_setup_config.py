from unittest.mock import MagicMock
import pytest
from aw_cli.cli.setup_config import setup_config

def test_setup_config(monkeypatch):
    # Mock di Fzf().run per simulare le risposte interattive dell'utente
    fzf_mock = MagicMock()
    fzf_mock.run.side_effect = [
        "mpv",          # Scegli il player predefinito
        "sì",           # Mostrare gli episodi speciali?
        "animeunity",   # Scegli il provider
        "sì",           # Aggiornare automaticamente con AniList?
        "sì",           # Votare l'anime una volta completato?
        "sì",           # Mettere tra i preferiti una volta completato?
        "sì",           # Droppare l'anime una volta rimosso dalla cronologia?
    ]
    monkeypatch.setattr("aw_cli.cli.setup_config.Fzf", lambda: fzf_mock)

    # Mock di env.open_url
    open_url_mock = MagicMock()
    monkeypatch.setattr("aw_cli.cli.setup_config.env.open_url", open_url_mock)

    # Mock di env.supports_syncplay per abilitare la parte di configurazione di syncplay
    from aw_cli.core.env import env
    monkeypatch.setattr(env.__class__, "supports_syncplay", property(lambda self: True))

    # Mock di Prompt.ask per simulare l'inserimento del token di AniList
    prompt_ask_mock = MagicMock()
    prompt_ask_mock.side_effect = [
        "mock_anilist_token",
    ]
    monkeypatch.setattr("rich.prompt.Prompt.ask", prompt_ask_mock)

    # Mock di shutil.which per far credere che player e syncplay siano installati nel sistema
    def my_which(cmd):
        if cmd in ("mpv", "vlc"):
            return "/usr/bin/mpv"
        if cmd == "syncplay":
            return "/usr/bin/syncplay"
        return None
    which_mock = MagicMock(side_effect=my_which)
    monkeypatch.setattr("shutil.which", which_mock)

    # Mock della query API di anilist per recuperare l'id utente
    monkeypatch.setattr("aw_cli.core.anilist.get_user_id", lambda token: 98765)

    # Mock di config.save per intercettare i dati che vengono scritti su file
    save_mock = MagicMock()
    monkeypatch.setattr("aw_cli.cli.setup_config.config.save", save_mock)

    # Eseguiamo il setup
    setup_config()

    # Verifichiamo che config.save sia stato chiamato una volta con i parametri inseriti
    save_mock.assert_called_once()
    saved_config = save_mock.call_args[0][0]

    assert saved_config["player"]["type"] == "mpv"
    assert saved_config["player"]["path"] == "/usr/bin/mpv"
    assert saved_config["general"]["specials"] is True
    assert saved_config["provider"]["source"] == "animeunity"
    assert saved_config["anilist"]["token"] == "mock_anilist_token"
    assert saved_config["anilist"]["user_id"] == 98765
    assert saved_config["anilist"]["rating"] is True
    assert saved_config["anilist"]["favorite"] is True
    assert saved_config["anilist"]["drop"] is True
    assert saved_config["syncplay"]["path"] == "/usr/bin/syncplay"

    # Verifica che il browser sia stato aperto per l'autenticazione AniList
    open_url_mock.assert_called_once_with("https://anilist.co/api/v2/oauth/authorize?client_id=11388&response_type=token")
