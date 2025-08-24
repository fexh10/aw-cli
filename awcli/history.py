import json
import os
import awcli.utilities as ut
from awcli.anime import Anime, Episode

anime_log = list[Anime]()

def read():
    """
    Legge la cronologia da un file json.

    Returns:
        list[Anime]: la lista degli anime trovati
    """
    global anime_log
    try:
        with open(f"{os.path.dirname(__file__)}/history.json", encoding='utf-8') as file:
            data = json.load(file)
    except FileNotFoundError:
        anime_log = legacy()
        save() # Crea il file se non lo trova
        return []

    for entry in data:
        anime = Anime(
            name=entry["name"],
            url=entry["url"],
            curr_ep=entry["curr_ep"],
            last_ep=entry["last_ep"]
        )
        anime._update_episodes(
            {ep["num"]: ep["ref"] for ep in entry["episodes"]}, 
            specials=ut.configData["general"]["specials"]
        )
        for ep in entry["episodes"]:
            anime.episode(ep["num"]).progress = ep["progress"]
            anime.episode(ep["num"]).completed = ep["completed"]

        anime._set_info(entry["id_anilist"], entry["info"])
        anime_log.append(anime)

def get() -> list[Anime]:
    """
    Prende i dati dalla cronologia.

    Returns:
        list[Anime]: la lista degli anime trovati 

    """
    if len(anime_log) == 0:
        ut.my_print("Cronologia inesistente!", color='rosso')
        exit()  
    return anime_log

def reload(last_releases: list[Anime]):
    """
    Aggiorna la cronologia degli anime con le ultime uscite disponibili.

    Questa funzione esamina ciascun anime nella cronologia e verifica se sono disponibili nuove uscite.
    Se trova nuove uscite per un anime, ne aggiorna lo stato.

    Args:
        last_releases (list[Anime]): La lista degli ultimi anime rilasciati.
    """
    global anime_log
    if "0" not in [anime.info["Stato"] for anime in anime_log]:
        return  # Nessun anime in corso, esco subito
    
    for i, anime in reversed(list(enumerate(anime_log))):
        for anime_latest in last_releases:
            if anime.name == anime_latest.name and anime.curr_ep != anime_latest.last_ep:
                anime._update_episodes({num: anime_latest.episode(num).ref for num in anime_latest.episodes()})
                break

def update(anime: Anime, episode: Episode):
    """
    Aggiorna la cronologia.

    Args:
        anime (Anime): l'anime da aggiornare.
        episode (Episode): l'episodio da aggiornare.
    """
    global anime_log
    anime_log.remove(anime) if anime in anime_log else None
    last_completed = episode.is_completed() and episode.num == anime.last_ep
    if anime.info["Stato"] == "1" and last_completed:
        return

    if last_completed:
        anime_log.append(anime)
    else:
        anime_log.insert(0, anime)

def save() -> None:
    """
    Salva la cronologia su un file JSON.
    """
    with open(f"{os.path.dirname(__file__)}/history.json", 'w', encoding='utf-8') as file:
        json.dump(
            [anime.to_dict() for anime in anime_log],
            file,
            ensure_ascii=False,
            indent=4
        )

def legacy() -> list[Anime]:
    """
    Legge i dati dalla vecchia cronologia in csv
    """
    import csv
    try:
        with open(f"{os.path.dirname(__file__)}/aw-cronologia.csv", encoding='utf-8') as file:
            legacy = [riga for riga in csv.reader(file)]
    except FileNotFoundError:
        pass
    if not legacy:
        return []

    animes = []
    for riga in legacy:
        if len(riga) < 4:
            riga.append("??")
        if len(riga) < 5:
            riga.append(0)
        if len(riga) < 6:
            riga.append(riga[1])    
        if len(riga) < 7:
            riga.append(0)
        if len(riga) < 8:
            riga.append(0)
        anime = Anime(name=riga[0], url=riga[2], curr_ep=riga[1], last_ep=riga[5])
        anime._update_episodes({anime.curr_ep: "Not available"}, ut.configData["general"]["specials"])
        if (progress := int(riga[7])) == 0:
            anime.episode(anime.curr_ep).mark_completed()
        else:
            anime.episode(anime.curr_ep).set_progress(progress)
        anime._set_info(int(riga[6]), {"Episodi": riga[3], "Stato": riga[4]})
        animes.append(anime)

    return animes
