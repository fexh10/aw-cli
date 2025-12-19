import json
from pathlib import Path
from . import utilities as ut
from .anime import Anime, AnimeStatus

class History:

    """
    Classe che gestisce la cronologia degli anime.
    """
    def __init__(self, path: str = "", anime_log: list[Anime] = []):
        self._path = path
        self._anime_log = anime_log

    @classmethod
    def read(cls, path: str) -> "History":
        """
        Legge la cronologia da un file json.

        Args:
            path (str): il percorso della cartella contenente il file history.json.

        Returns:
            History: l'oggetto History con i dati letti dal file.
        """
        anime_log = []
        history_path = Path(path) / "history.json"
        try:
            with open(history_path, encoding='utf-8') as file:
                anime_log = [Anime.from_dict(entry) for entry in json.load(file)]
        except FileNotFoundError:
            anime_log = legacy()

        return cls(str(history_path), anime_log)

    def get(self) -> list[Anime]:
        """
        Prende i dati dalla cronologia.

        Returns:
            list[Anime]: la lista degli anime trovati

        """
        return self._anime_log

    def remove(self, Anime: Anime) -> None:
        """
        Rimuove un anime dalla cronologia.

        Args:
            Anime (Anime): l'anime da rimuovere.
        """
        self._anime_log.remove(Anime)
        self.save()

    def reload(self, last_releases: list[Anime]) -> None:
        """
        Aggiorna la cronologia degli anime con le ultime uscite disponibili.

        Questa funzione esamina ciascun anime nella cronologia e verifica se sono disponibili nuove uscite.
        Se trova nuove uscite per un anime, ne aggiorna lo stato.

        Args:
            last_releases (list[Anime]): La lista degli ultimi anime rilasciati.
        """
        if AnimeStatus.ONGOING not in [anime.status for anime in self._anime_log]:
            return

        for anime in reversed(self._anime_log):
            for anime_latest in last_releases:
                if anime == anime_latest and anime.last_ep != anime_latest.last_ep:
                    anime.update_episodes({
                        num: anime_latest.episode(num).ref
                        for num in anime_latest.episodes()
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
        self._anime_log.remove(anime) if anime in self._anime_log else None
        last_completed = episode.is_completed() and episode.num == anime.last_ep
        if anime.status == AnimeStatus.FINISHED and last_completed:
            self.save()
            return

        if last_completed:
            self._anime_log.append(anime)
        else:
            self._anime_log.insert(0, anime)

        self.save()

    def save(self) -> None:
        """
        Salva la cronologia su un file JSON.
        """
        with open(self._path, 'w', encoding='utf-8') as file:
            json.dump(
                [anime.to_dict() for anime in self._anime_log],
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
        with open(Path(__file__).parent / "aw-cronologia.csv", encoding='utf-8') as file:
            legacy = [riga for riga in csv.reader(file)]
    except FileNotFoundError:
        pass
    if not legacy:
        return []

    animes = []
    for row in legacy:
        if len(row) < 4:
            row.append("??")
        if len(row) < 5:
            row.append("0")
        if len(row) < 6:
            row.append(row[1])
        if len(row) < 7:
            row.append("0")
        if len(row) < 8:
            row.append("0")
        anime = Anime(name=row[0], ref=row[2], curr_ep=row[1], last_ep=row[5])
        anime.update_episodes({anime.curr_ep: "Not available"}, ut.config_data["general"]["specials"])
        episode = anime.episode(anime.curr_ep)
        if episode:
            if (progress := int(row[7])) == 0:
                episode.mark_completed()
            else:
                episode.set_progress(progress)
        anime.set_info(int(row[6]), list(AnimeStatus)[int(row[4])], {"Episodi": row[3]})
        animes.append(anime)

    return animes
