import json
import os
from . import utilities as ut
from .anime import Anime, AnimeStatus

class History:

    """
    Modulo per gestire la cronologia degli anime.
    """
    def __init__(self):
        self.anime_log = list[Anime]()
        try:
            self.read()
        except FileNotFoundError:
            self.anime_log = legacy()
            self.save() # Crea il file se non lo trova

    def read(self):
        """
        Legge la cronologia da un file json.

        Returns:
            list[Anime]: la lista degli anime trovati
        """
        with open(f"{os.path.dirname(__file__)}/history.json", encoding='utf-8') as file:
            data = json.load(file)

        for entry in data:
            anime = Anime(
                name=entry["name"],
                ref=entry["ref"],
                curr_ep=entry["curr_ep"],
                last_ep=entry["last_ep"]
            )
            anime.update_episodes(
                {ep["num"]: ep["ref"] for ep in entry["episodes"]}, 
                specials=ut.configData["general"]["specials"]
            )
            for ep in entry["episodes"]:
                episode = anime.episode(ep["num"])
                if episode:
                    episode.progress = ep["progress"]
                    episode.completed = ep["completed"]

            
            match entry["info"].get("Stato", "").lower():
                case "in corso":
                    status = AnimeStatus.ONGOING
                case "finito":
                    status = AnimeStatus.FINISHED
                case "non rilasciato":
                    status = AnimeStatus.NOT_RELEASED
                case _:
                    status = AnimeStatus.UNKNOWN

            anime.set_info(entry["id_anilist"], status, entry["info"])
            self.anime_log.append(anime)

    def get(self) -> list[Anime]:
        """
        Prende i dati dalla cronologia.

        Returns:
            list[Anime]: la lista degli anime trovati 

        """
        if len(self.anime_log) == 0:
            ut.my_print("Cronologia inesistente!", color='rosso')
            exit()  
        return self.anime_log
    
    def remove(self, Anime: Anime) -> None:
        """
        Rimuove un anime dalla cronologia.

        Args:
            Anime (Anime): l'anime da rimuovere.
        """
        self.anime_log.remove(Anime)
        self.save()

    def reload(self, last_releases: list[Anime]):
        """
        Aggiorna la cronologia degli anime con le ultime uscite disponibili.

        Questa funzione esamina ciascun anime nella cronologia e verifica se sono disponibili nuove uscite.
        Se trova nuove uscite per un anime, ne aggiorna lo stato.

        Args:
            last_releases (list[Anime]): La lista degli ultimi anime rilasciati.
        """
        global anime_log
        if AnimeStatus.ONGOING not in [anime.status for anime in self.anime_log]:
            return

        for _, anime in reversed(list(enumerate(self.anime_log))):
            for anime_latest in last_releases:
                if anime == anime_latest and anime.last_ep != anime_latest.last_ep:
                    anime.update_episodes({
                        num: ep.ref
                        for num in anime_latest.episodes() 
                        if (ep := anime_latest.episode(num)) is not None
                    })
                    break
        self.save()

    def update(self, anime: Anime, episode: Anime.Episode):
        """
        Aggiorna la cronologia.

        Args:
            anime (Anime): l'anime da aggiornare.
            episode (Anime.Episode): l'episodio da aggiornare.
        """
        self.anime_log.remove(anime) if anime in self.anime_log else None
        last_completed = episode.is_completed() and episode.num == anime.last_ep
        if anime.status == AnimeStatus.FINISHED and last_completed:
            self.save()
            return

        if last_completed:
            self.anime_log.append(anime)
        else:
            self.anime_log.insert(0, anime)

        self.save()

    def save(self) -> None:
        """
        Salva la cronologia su un file JSON.
        """
        with open(f"{os.path.dirname(__file__)}/history.json", 'w', encoding='utf-8') as file:
            json.dump(
                [anime.to_dict() for anime in self.anime_log],
                file,
                ensure_ascii=False,
                indent=4
            )

def legacy() -> list[Anime]:
    """
    Legge i dati dalla vecchia cronologia in csv
    """
    import csv
    legacy = []
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
            riga.append("0")
        if len(riga) < 6:
            riga.append(riga[1])    
        if len(riga) < 7:
            riga.append("0")
        if len(riga) < 8:
            riga.append("0")
        anime = Anime(name=riga[0], ref=riga[2], curr_ep=riga[1], last_ep=riga[5])
        anime.update_episodes({anime.curr_ep: "Not available"}, ut.configData["general"]["specials"])
        episode = anime.episode(anime.curr_ep)
        if episode:
            if (progress := int(riga[7])) == 0:
                episode.mark_completed()
            else:
                episode.set_progress(progress)
        anime.set_info(int(riga[6]), list(AnimeStatus)[int(riga[4])], {"Episodi": riga[3]})
        animes.append(anime)

    return animes
