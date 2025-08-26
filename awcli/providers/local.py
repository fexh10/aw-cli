import os
from awcli import history
from awcli.providers.provider import Provider, Anime, Episode


class LocalProvider(Provider):
    """
    Class for offline mode.
    """
    def __init__(self, path: str):
        super().__init__(path)

    def _search(self, input: str) -> list[Anime]:
        results = []
        for name in os.listdir(self.BASE_URL):
            if not (input == "" or input.lower() in name.lower()):
                continue
            anime = Anime(name, f"{self.BASE_URL}/{name}")
            if anime in history.get():
                self.episodes(anime)
                anime.curr_ep = anime.episodes()[0]
                self.info_anime(anime)
                results.append(anime)
        return results

    def _latest(self, filter: str, specials: bool) -> list[Anime]:
        for anime in (animes := self._search(filter)):
            anime.curr_ep = anime.episodes()[-1]
        return animes

    def _episodes(self, anime: Anime) -> dict[str, str]:
        filenames = os.listdir(anime.url)
        if len(filenames) == 0:
            return
        
        episodes_url = dict[str, str]()
        for filename in filenames:
            num = filename.split("Ep. ")[1].split(".mp4")[0]
            episodes_url[num] = filename
        return episodes_url

    def _episode_link(self, anime: Anime, episode: Episode) -> str:
        return f"{anime.url}/{episode.ref}"

    def _info_anime(self, anime: Anime) -> dict:
        other = history.get()[history.get().index(anime)]
        anime._set_info(other.id_anilist, other.info)
