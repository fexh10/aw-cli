import shutil
import toml
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from rich.prompt import Prompt

from ..core.env import env
from ..core.config import config
from ..core import anilist
from ..interface import Fzf, console

def setup_config() -> None:
    """
    Crea un file di configurazione chiamato "config.toml"
    nella stessa directory dello script.
    Le informazioni riportate saranno scelte dall'utente.
    Sarà possibile scegliere il Player predefinito,
    se collegare il proprio profilo AniList e
    se inserire il path di syncplay.
    """
    config_data = config._defaults.copy()
 
    # player predefinito
    console.clear()
    console.print("AW-CLI - CONFIGURAZIONE", style="info")

    config_data["player"]["type"] = Fzf().run(
        ["vlc", "mpv"], "Scegli il player predefinito: "
    )
    if env.supports_syncplay:
        path = shutil.which(config_data["player"]["type"])
        if path is None:
            console.print(
                f"Player {config_data['player']['type']} non trovato!", style="error"
            )
            config_data["player"]["path"] = Prompt.ask(
                f"Inserisci il path di {config_data['player']['type']} manualmente se è installato",
                console=console,
            )
        else:
            config_data["player"]["path"] = path
        console.clear()
        console.print("AW-CLI - CONFIGURAZIONE", style="info")

    config_data["general"]["specials"] = (
        Fzf().run(["sì", "no"], "Mostrare gli episodi speciali? ") == "sì"
    )

    # provider preferito
    config_data["provider"]["source"] = Fzf().run(
        ["animeunity", "animeworld"], "Scegli il provider: "
    )

    # anilist
    if (
        Fzf().run(["sì", "no"], "Aggiornare automaticamente la watchlist con AniList? ")
        == "sì"
    ):
        link = "https://anilist.co/api/v2/oauth/authorize?client_id=11388&response_type=token"
        env.open_url(link)

        # inserimento token
        console.clear()
        config_data["anilist"]["token"] = Prompt.ask(
            f"Inserire il token di AniList ({link})", console=console
        )

        # prendo l'id dell'utente tramite query
        with ThreadPoolExecutor() as executor:
            (
                config_data["anilist"]["rating"],
                config_data["anilist"]["favorite"],
                config_data["anilist"]["drop"],
            ) = False, False, False
            future = executor.submit(
                anilist.get_user_id, config_data["anilist"]["token"]
            )
            console.clear()
            console.print("AW-CLI - CONFIGURAZIONE", style="info")
            if Fzf().run(["sì", "no"], "Votare l'anime una volta completato? ") == "sì":
                config_data["anilist"]["rating"] = True

            if (
                Fzf().run(
                    ["sì", "no"],
                    "Chiedere se mettere l'anime tra i preferiti una volta completato? ",
                )
                == "sì"
            ):
                config_data["anilist"]["favorite"] = True

            if (
                Fzf().run(
                    ["sì", "no"],
                    "Chiedere se droppare l'anime una volta rimosso dalla cronologia? ",
                )
                == "sì"
            ):
                config_data["anilist"]["drop"] = True

            config_data["anilist"]["user_id"] = future.result()

    # syncplay
    if env.supports_syncplay:
        syncplay_path = shutil.which("syncplay")
        if syncplay_path is None:
            console.print("Syncplay non trovato!", style="error")
            syncplay = Prompt.ask(
                "Inserisci il path di Syncplay (premere INVIO se non lo si desidera utilizzare)",
                console=console,
            ).replace("Program Files (x86)", "Progra~2")
            if syncplay != "":
                config_data["syncplay"]["path"] = syncplay
        else:
            config_data["syncplay"]["path"] = syncplay_path

    # creo il file
    config.save(config_data)