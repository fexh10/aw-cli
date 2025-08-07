import re
import requests
from html import unescape
from awcli.providers.provider import Provider, Anime, Episode
from awcli import utilities as ut

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
        self._cookies = {}
        self._visited = {}
    
    def _get_html(self, url: str) -> str:
        """
        Ottiene l'html della pagina web `url`.
        Se la pagina non viene trovata o c'è un errore di connessione, 
        viene stampato un messaggio di errore e il programma termina.
        Se la pagina viene reindirizzata, vengono aggiornati i `cookies` e viene ripetuta la richiesta.

        Args:
            url (str): la pagina web da cui prendere l'html.

ImportError: cannot import name 'Anime' from par
        Returns:
            str: l'html della pagina web selezionata.
        """
        if url in self._visited:
            return self._visited[url]
        try:
            response = requests.get(url, headers=self._headers, cookies=self._cookies)
        except requests.exceptions.ConnectionError:
            ut.my_print("Errore di connessione", color="rosso")
            exit()

        if response.status_code == 202: 
            ut.my_print("Reindirizzamento...", color="giallo", end="\n") 
            match = re.search(r'(SecurityAW-\w+)=(.*) ;', response.text)
            self._cookies = {match.group(1): match.group(2)}    
            response = requests.get(url, headers=self._headers, cookies=self._cookies)
        
        if response.status_code != 200:
            ut.my_print("Errore: pagina non trovata", color="rosso")
            exit()
        if "Errore 404" in response.text:
            raise requests.exceptions.ConnectionError("Errore 404: pagina non trovata")
        
        self._visited[url] = response.text
        return response.text    

    def search(self, input: str) -> list[Anime]:
        ut.my_print("Ricerco...", color="giallo")
        search_url = self._url + "/search?keyword=" + input.replace(" ", "+")
        html = self._get_html(search_url)
        if re.search(r'<div class="alert alert-danger">', html):
            return []

        animes = list[Anime]()
        # prendo i link degli anime relativi alla ricerca
        for url, name in re.findall(r'<div class="inner">(?:.|\n)+?<a href="([^"]+)"\s+data-jtitle="[^"]+"\s+class="name">([^<]+)', html):
            if ut.nome_os == "Android":
                forbidden_char = '"*/:<>?\|'
                replace_char = '”⁎∕꞉‹›︖＼⏐'
                for a, b in zip(forbidden_char, replace_char):
                    name = name.replace(a, b)
            animes.append(Anime(unescape(name), self._url+url))
        
        return animes
    
    def latest(self, filter = "all") -> list[Anime]:
        html = self._get_html(self._url)
        animes = list[Anime]()

        for url, name, ep in re.findall(r'<a[\n\s]+href="([^"]+)"\n\s+class="poster" data-tip="[^"]+"\n\s+title="([^"]+) Ep ([^"]+)">', html):
            if ".5" not in ep:
                animes.append(Anime(unescape(name), self._url + url, int(ep)))
                
        match filter[0]:
            case 's': return animes[45:90]
            case 'd': return animes[90:135]
            case 't': return animes[135:]
            case  _ : return animes[:45]

    def _get_anime(self, anime):
        """
        Ottiene il riferimento dell'anime.
        
        Se il riferimento non è valido, cerca l'anime per nome e aggiorna il riferimento.
        """
        try:
            html = self._get_html(anime.url)
        except requests.exceptions.ConnectionError:
            ut.my_print("Il link è stato cambiato", color="rosso", end="\n")
            anime.url = self._search(anime.name)[0].url
            html = self._get_html(anime.url)
        return html

    def episodes(self, anime: Anime):
        html = self._get_anime(anime)
        episodes_url = list[str]()
        for num, url in re.findall(r'<a.+data-num="([^"]+)".+href="([^"]+)"', html):
            if num.endswith(".5") or num == "0":
                continue
            nums = num.split("-")
            for num in nums:
                if int(num) <= len(episodes_url):
                    continue
                episodes_url.append(self._url + url)
        anime._set_episodes(episodes_url)


    def episode_link(self, episode: Episode) -> str:
        pattern = r'<a\s+href="([^"]+)"\s+id="alternativeDownloadLink"'
        res = re.search(pattern, self._get_html(episode.ref)) 
        if res:
            return res.group(1)
        exit()
    
    
    def info_anime(self, anime: Anime):
        html = self._get_anime(anime)

        res = re.search(r'<a.*id="anilist-button".*href="\D*(\d*)"', html)
        anilist_id = int(res.group(1)) if res else 0
        
        temp = re.findall(r'<dt>(.*?):</dt>[\n\s]*<dd(?: class="[^"]*")?>((?:.|\n)+?)</dd>', html)
        temp.append(("Trama", re.search(r'<div class="desc">((?:.|\n)+?)</div>', html).group(1)))

        info = dict[str, str]()
        for key, value in temp:
            key, value = key.strip(), value.strip()
            if key == "Stato":
                value = re.search(r'<a.*href="[^"]*status=(\d+)"', value).group(1)
            else:
                value = re.sub(r'[\s\n]+', ' ', re.sub(r'<.*?>', '', value)).strip()
            info[key] = unescape(value)

        anime._set_info(anilist_id, info)