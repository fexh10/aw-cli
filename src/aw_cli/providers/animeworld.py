from functools import lru_cache
import re
from html import unescape
from urllib.parse import quote_plus
from ..anime import Anime, AnimeStatus
from .provider import Provider, HTTPError

class Animeworld(Provider):
    """
    Classe che gestisce il collegamento con Animeworld.

    Attributes:
        _url (str): l'url del sito di Animeworld.
        _headers (dict): gli headers da utilizzare per le richieste HTTP.
        _cookies (dict): i cookies da utilizzare per le richieste HTTP.
        _visited (dict): le pagine già visitate.
    """
    def __init__(self, client=None):
        super().__init__("https://www.animeworld.ac", client=client)
        self._visited = {}

    @lru_cache
    def _get_html(self, url: str) -> str:
        """
        Ottiene l'html della pagina web `url`.
        Se la pagina non viene trovata o c'è un errore di connessione,
        viene stampato un messaggio di errore e il programma termina.
        Se la pagina viene reindirizzata, vengono aggiornati i `cookies` e viene ripetuta la richiesta.

        Args:
            url (str): la pagina web da cui prendere l'html.

        Returns:
            str: l'html della pagina web selezionata.
        """
        if not re.match(r'^https?://', url):
            raise HTTPError("Errore 404: pagina non trovata")

        response = self.Client.get(url)
        response.raise_for_status()

        if response.status_code == 202:
            match = re.search(r'(SecurityAW-\w+)=(.*) ;', response.text)
            if not match:
                raise HTTPError("Errore: Cookies non trovati")
            self.Client.cookies.set(match.group(1), match.group(2))
            response = self.Client.get(url)

        if response.status_code != 200 or "Errore 404" in response.text:
            raise HTTPError("Errore 404: pagina non trovata")

        return response.text

    def _search(self, input: str) -> list[Anime]:
        search_url = self.BASE_URL + "/search?keyword=" + quote_plus(input)
        html = self._get_html(search_url)
        if re.search(r'<div class="alert alert-danger">', html):
            return []

        animes = list[Anime]()
        # Split by the result item container to avoid giant regex backtracking
        items = html.split('<div class="item">')[1:]
        for item in items:
            # Extract URL and Name within each item block
            match = re.search(r'<a href="([^"]+)"[^>]*class="name"[^>]*>([^<]+)</a>', item)
            if match:
                url, name = match.groups()
                animes.append(Anime(unescape(name), self.BASE_URL + url))

        return animes

    def _latest(self, filter: str, specials: bool) -> list[Anime]:
        html = self._get_html(self.BASE_URL)
        animes = list[Anime]()

        for url, name, ep in re.findall(r'<a[\n\s]+href="([^"]+)"\n\s+class="poster" data-tip="[^"]+"\n\s+title="([^"]+) Ep ([^"]+)">', html):
            anime = Anime(unescape(name), self.BASE_URL + url, ep)
            anime.update_episodes({ep: self.BASE_URL + url}, specials=specials)
            animes.append(anime)

        BLOCK_SIZE = 45
        filter_keys = ['a', 's', 'd', 't']
        multiplier = filter_keys.index(filter[0])

        start = multiplier * BLOCK_SIZE
        end = (multiplier + 1) * BLOCK_SIZE if multiplier < len(filter_keys) else None

        return animes[start:end]

    def _episodes(self, anime: Anime):
        html = self._get_html(anime.ref)
        episodes_url = dict[str, str]()
        for num, url in re.findall(r'<a.+data-num="([^"]+)".+href="([^"]+)"', html):
            episodes_url[num] = self.BASE_URL + url
        return episodes_url

    def _episode_link(self, anime: Anime, episode: Anime.Episode) -> str:
        pattern = r'<a\s+href="([^"]+)"\s+id="alternativeDownloadLink"'
        html = self._get_html(episode.ref)
        res = re.search(pattern, html)
        if not res:
            raise ValueError("Errore nel parsing della pagina dell'episodio")
        return res.group(1)

    def _info_anime(self, anime: Anime):
        html = self._get_html(anime.ref)

        res = re.search(r'<a.*id="anilist-button".*href="\D*(\d*)"', html)
        anilist_id = int(res.group(1)) if res else 0

        temp = re.findall(r'<dt>(.*?):</dt>[\n\s]*<dd(?: class="[^"]*")?>((?:.|\n)+?)</dd>', html)
        plot_match = re.search(r'<div class="desc">((?:.|\n)+?)</div>', html)
        if plot_match:
            temp.append(("Trama", plot_match.group(1)))

        info = dict[str, str]()
        status = AnimeStatus.UNKNOWN
        for key, value in temp:
            key, value = key.strip(), value.strip()
            if key == "Stato":
                if match := re.search(r'status=(\d+)"', value):
                    status_val = int(match.group(1))
                    if status_val < len(AnimeStatus):
                        status = list(AnimeStatus)[status_val]
            value = re.sub(r'[\s\n]+', ' ', re.sub(r'<.*?>', '', value)).strip()
            info[key] = unescape(value)

        anime.set_info(anilist_id, status, info)
