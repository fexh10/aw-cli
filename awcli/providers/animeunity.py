import re
import requests
import json
from html import unescape
from functools import lru_cache
from awcli.providers.provider import Provider, Anime, Episode
from awcli import utilities as ut

class Animeunity(Provider):
    """
    Classe che gestisce il collegamento con Animeworld.
    
    Attributes:
        _url (str): l'url del sito di Animeworld.
        _headers (dict): gli headers da utilizzare per le richieste HTTP.
        _cookies (dict): i cookies da utilizzare per le richieste HTTP.
        _visited (dict): le pagine già visitate.
    """
    def __init__(self):
        super().__init__("https://www.animeunity.so")
        self._cookies = {}
        self._visited = {}

    @lru_cache
    def _get_token(self) -> None:
        # Send a GET request to the specified URL
        response = requests.get(self._url, headers=self._headers, cookies=self._cookies)
        self.html = response.text
        # Regex to find the meta tag with csrf-token and extract the content
        csrf_match = re.search(r'<meta.*?name="csrf-token".*?content="([^"]*)".*?>', self.html)
        if not csrf_match:
            ut.my_print("Errore nel recupero del token CSRF", color="rosso")
            exit()
        csrf_token = csrf_match.group(1)
        self._headers['x-csrf-token'] = csrf_token
        self._cookies['animeunity_session'] = response.cookies.get('animeunity_session')
    
    
    def search(self, input: str) -> list[Anime]:
        ut.my_print("Ricerco...", color="giallo")
        search_url = f"{self._url}/livesearch"
        self._get_token()  # Assicura che i token/cookie siano aggiornati
        try:
            response = requests.post(
            url=search_url,
            data={"title": input},
            cookies=self._cookies,
            headers=self._headers,
            timeout=10
            )
            response.raise_for_status()
        except Exception as e:
            ut.my_print(f"Errore nella richiesta di ricerca: {e}", color="rosso")
            return []

        results = response.json()['records']
        animes = list[Anime]()
        for result in results:
            title, anilist_id, info = self._parse_info(result)
            anime = Anime(title, result['id'])
            anime._set_info(anilist_id, info)
            animes.append(anime)

        return animes
       

    def latest(self, filter="all") -> list[Anime]:
        self._get_token()
        regex = re.search(r'<layout-items[^>]*items-json="([^"]*)"', self.html)
    
        if not regex:
            ut.my_print("Nessun elemento trovato", color="rosso")
            exit()

        data_attribute = unescape(regex.group(1))
        json_data = json.loads(data_attribute)['data']
        animes = list[Anime]()
        for data in json_data:
            result = data['anime']
            title, anilist_id, info = self._parse_info(result)
            if filter == "d" and info["Audio"] != "Italiano":
                continue
            if filter == "s" and info["Audio"] == "Italiano":
                continue
            anime = Anime(title, result['id'], str(data['number']))
            anime._set_info(anilist_id, info)
            animes.append(anime)
        return animes
        
    def episodes(self, anime: Anime):
        episode_count = max(int(anime.info["Episodi"] if anime.info["Episodi"].isdigit() else int(anime.curr_ep)), int(anime.last_ep))
        if episode_count < 1:
            self.info_anime(anime)
            episode_count = int(anime.info["Episodi"])
        episodi = {}
        start_range = 1
        # Fetch episodes in chunks
        while start_range <= episode_count:
            end_range = min(start_range + 119, episode_count)
            search_url = f"{self._url}/info_api/{anime.url}/1"
            self._get_token()  # Assicura che i token/cookie siano aggiornati
            try:
                response = requests.get(
                url=search_url,
                params={
                    "start_range": start_range,
                    "end_range": end_range
                },
                cookies=self._cookies,
                headers=self._headers,
                timeout=10
                )
                response.raise_for_status()
            except requests.exceptions.HTTPError:
                ut.my_print("Il link è stato cambiato", color="rosso", end="\n")
                anime.url = self.search(anime.name)[0].url
                return self.episodes(anime)  # Retry with the new URL
            except Exception as e:
                ut.my_print(f"Errore nella richiesta degli episodi: {e}", color="rosso")
                exit()
            #episodi = {episode['number']: episode['id'] for episode in response.json()['episodes']}
            episodi.update({episode['number']: episode['id'] for episode in response.json()['episodes']})
            start_range = end_range + 1
        anime._set_episodes(episodi)

    def episode_link(self, episode: Episode) -> str:
        try:
            embed_url = f"{self._url}/embed-url/{episode.ref}"
            response = requests.get(embed_url, headers=self._headers, cookies=self._cookies, timeout=10)
            response.raise_for_status()

            # The embed URL is returned as plain text
            iframe_src = response.text.strip()

            # Fetch the video page
            video_response = requests.get(iframe_src, headers=self._headers, cookies=self._cookies, timeout=10)
            video_response.raise_for_status()

            # Usa una regex per estrarre il link video MP4 dallo script
            match = re.search(r"window.downloadUrl\s*=\s*'([^']*)", video_response.text)
            if not match:
                ut.my_print("Errore nel parsing del link video", color="rosso")
                exit()
            src_mp4 = match.group(1)
            return src_mp4

        except Exception as e:
            ut.my_print(f"Errore nel recupero del link episodio: {e}", color="rosso")
            exit()

    def info_anime(self, anime: Anime):
        search_url = f"{self._url}/info_api/{anime.url}/"
        self._get_token()  # Assicura che i token/cookie siano aggiornati
        try:
            response = requests.get(
            url=search_url,
            cookies=self._cookies,
            headers=self._headers,
            timeout=10
            )
            response.raise_for_status()
        except Exception as e:
            ut.my_print(f"Errore nella richiesta di info anime: {e}", color="rosso")
            exit()
        data = response.json()
        anime.info["Episodi"] = str(data['episodes_count']) 
        anime.info["Genere"] = ', '.join(data['genres'])
        anime.info["Correlati"] = data['related']
        

    def _parse_info(self, data: dict) -> tuple[str, str, dict[str, str]]:
        title = data['title_eng'] or data['title'] or data['title_it']
        anilist_id = data['anilist_id']
        info = {
            "Categoria": data['type'],
            "Audio": "Italiano" if data['dub'] else "??",
            "Data di Uscita": data['date'],
            "Stagione": data['season'],
            "Studio": data['studio'],
            "Voto": data['score'],
            "Durata": f"{data['episodes_length']} min",
            "Episodi": str(data['episodes_count']),
            "Stato": "0" if data['status'] == "In Corso" else "1" if data['status'] == "Terminato" else "2",
            "Visualizzazioni": data['visite'],
            "Trama": data['plot'],
        }
        return title, anilist_id, info
