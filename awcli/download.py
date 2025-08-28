import os
from pathlib import Path
from pySmartDL import SmartDL
from awcli import utilities as ut
from awcli.anime import Anime
from awcli.providers.provider import Provider


def path(create: bool = True) -> str:
    """
    Restituisce il percorso di download dell'anime, a seconda del sistema operativo in uso.
    Se create è True (valore predefinito) e il percorso non esiste, viene creato.

    Args:
        create (bool, optional): se impostato a True, crea il percorso se non esiste. Valore predefinito: True.

    Returns:
        str: il percorso di download dell'anime.
    """

    if (ut.nome_os == "Android"):
        path = f"/sdcard/Movies/Anime"
    else:
        path = f"{Path.home()}/Videos/Anime"
    if create and not os.path.exists(path):
        os.makedirs(path)
    return path

def episode(anime: Anime, ep: Anime.Episode, provider: Provider, path: str):
    """
    Scarica l'episodio dell'anime e lo salva nella cartella specificata.
    Se l'episodio è già presente nella cartella, non viene riscaricato.

    Args:
        ep (Anime.Episode): L'episodio da scaricare.
        path (str): il percorso dove salvare l'episodio.
    """
    # se l'episodio non è ancora stato scaricato lo scarico, altrimenti skippo
    ut.my_print(str(ep), color="blu", end=":\n")
    if not os.path.exists(f"{path}/{ep}.mp4"):
        SDL = SmartDL(provider.episode_link(anime, ep), f"{path}/{ep}.mp4")
        SDL.start()
    else:
        ut.my_print("già scaricato, skippo...", color="giallo")
