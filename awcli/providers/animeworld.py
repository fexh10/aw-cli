from functools import lru_cache
import re
from html import unescape
from awcli.providers.provider import Provider, Anime, AnimeStatus, HTTPError

class Animeworld(Provider):
    """
    Classe che gestisce il collegamento con Animeworld.

    Attributes:
        _url (str): l'url del sito di Animeworld.
        _headers (dict): gli headers da utilizzare per le richieste HTTP.
        _cookies (dict): i cookies da utilizzare per le richieste HTTP.
        _visited (dict): le pagine già visitate.
    """
    def __init__(self):
        super().__init__("https://www.animeworld.ac")
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
            self.Client.cookies = {match.group(1): match.group(2)}
            response = self.Client.get(url)

        if response.status_code != 200 or "Errore 404" in response.text:
            raise HTTPError("Errore 404: pagina non trovata")

        return response.text    

    def _search(self, input: str) -> list[Anime]:
        search_url = self.BASE_URL + "/search?keyword=" + input.replace(" ", "+")
        html = self._get_html(search_url)
        if re.search(r'<div class="alert alert-danger">', html):
            return []

        animes = list[Anime]()
        # prendo i link degli anime relativi alla ricerca
        for url, name in re.findall(r'<div class="inner">(?:.|\n)+?<a href="([^"]+)"\s+data-jtitle="[^"]+"\s+class="name">([^<]+)', html):
            animes.append(Anime(unescape(name), self.BASE_URL+url))
        
        return animes

    def _latest(self, filter: str, specials: bool) -> list[Anime]:
        html = self._get_html(self.BASE_URL)
        animes = list[Anime]()

        for url, name, ep in re.findall(r'<a[\n\s]+href="([^"]+)"\n\s+class="poster" data-tip="[^"]+"\n\s+title="([^"]+) Ep ([^"]+)">', html):
            animes.append(Anime(unescape(name), self.BASE_URL + url, ep))
                
        match filter[0]:
            case 's': return animes[45:90]
            case 'd': return animes[90:135]
            case 't': return animes[135:]
            case  _ : return animes[:45]

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
        trama_match = re.search(r'<div class="desc">((?:.|\n)+?)</div>', html)
        if trama_match:
            temp.append(("Trama", trama_match.group(1)))

        info = dict[str, str]()
        status = AnimeStatus.UNKNOWN
        for key, value in temp:
            key, value = key.strip(), value.strip()
            if key == "Stato":
                match value:
                    case "In Corso":
                        status = AnimeStatus.ONGOING
                    case "Terminato":
                        status = AnimeStatus.FINISHED
                    case "Non Rilasciato":
                        status = AnimeStatus.NOT_RELEASED
                    case _:
                        status = AnimeStatus.UNKNOWN
            value = re.sub(r'[\s\n]+', ' ', re.sub(r'<.*?>', '', value)).strip()
            info[key] = unescape(value)

        anime.set_info(anilist_id, status, info)