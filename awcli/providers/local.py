
import os
from awcli.providers.provider import Provider, Anime, Episode

class LocalProvider(Provider):
    """
    Provider locale per la gestione degli anime scaricati.
    Permette di cercare, elencare e ottenere informazioni sugli anime presenti localmente.
    - search: cerca tra gli anime scaricati
    - latest: non implementata
    - episodes: carica gli episodi scaricati
    - episode_link: restituisce il path locale
    - info_anime: carica info dalla cronologia
    """
    def __init__(self, path, history: list[Anime]):
        super().__init__(path)
        self.history = history

    def _search(self, input: str) -> list[Anime]:
        """Restituisce gli anime scaricati localmente, ignorando l'input di ricerca."""
        animes = []
        for name in os.listdir(self.BASE_URL):
            anime = Anime(name, f"{self.BASE_URL}/{name}")
            if anime in self.history:
                self.episodes(anime)
                self.info_anime(anime)
                anime.curr_ep = anime.episodes()[0]
                animes.append(anime)
        return animes

    def _latest(self, filter="all", special: bool = False):
        for anime in (res :=self.search("")):
            anime.curr_ep = anime.last_ep
        return res

    def _episodes(self, anime: Anime) -> dict[str, str]:
        filenames = os.listdir(f"{self.BASE_URL}/{anime.name}")
        if len(filenames) == 0:
            return
        
        episodes = dict[str, str]()
        for filename in filenames:
            num = filename.split("Ep. ")[1].split(".mp4")[0]
            episodes[num] = filename
        return episodes

    def _episode_link(self, anime: Anime, episode: Episode) -> str:
        return f"{self.BASE_URL}/{anime.name}/{episode.ref}"

    def _info_anime(self, anime: Anime) -> dict:
        index = self.history.index(anime)
        anime_data = self.history[index]
        anime.url = anime_data.url
        anime._set_info(anime_data.id_anilist, anime_data.info)
        return anime.to_dict()