import re
import json
from html import unescape
from ..anime import Anime, AnimeStatus
from .provider import Provider, HTTPError

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
        self._get_token()  # Assicura che i token/cookie siano aggiornati

    
    def _get_token(self) -> None:
        # Send a GET request to the specified URL
        response = self.Client.get(self.BASE_URL)
        self.html = response.text
        # Regex to find the meta tag with csrf-token and extract the content
        csrf_match = re.search(r'<meta.*?name="csrf-token".*?content="([^"]*)".*?>', self.html)
        if not csrf_match:
            raise ValueError("CSRF token not found in the HTML")
        csrf_token = csrf_match.group(1)
        self.Client.headers['x-csrf-token'] = csrf_token
        self.Client.cookies['animeunity_session'] = response.cookies.get('animeunity_session') or ""


    def _search(self, input: str) -> list[Anime]:
        search_url = f"{self.BASE_URL}/livesearch"
        response = self.Client.post(
            url=search_url,
            data={"title": input}
        )
        response.raise_for_status()

        results = response.json()['records']
        animes = list[Anime]()
        for result in results:
            title, last_ep, anilist_id, status, info = self._parse_info(result)
            anime = Anime(title, str(result['id']), last_ep=last_ep)
            anime.set_info(anilist_id, status, info)
            animes.append(anime)

        return animes


    def _latest(self, filter, specials) -> list[Anime]:
        regex = re.search(r'<layout-items[^>]*items-json="([^"]*)"', self.html)
        if not regex:
            raise ValueError("Errore nel parsing della pagina principale")

        data_attribute = unescape(regex.group(1))
        json_data = json.loads(data_attribute)['data']
        animes = list[Anime]()
        for data in json_data:
            result = data['anime']
            title, _, anilist_id, status, info = self._parse_info(result)
            if filter == "d" and info["Audio"] != "Italiano":
                continue
            if filter == "s" and info["Audio"] == "Italiano":
                continue
            anime = Anime(title, str(result['id']), curr_ep=str(data['number']))
            anime.update_episodes({str(data['number']): str(data['id'])}, specials=specials)
            anime.set_info(anilist_id, status, info)
            animes.append(anime)
        return animes

    def _episodes(self, anime: Anime) -> dict[str, str]:
        episodi = {}
        start_range = 1
        episode_count = max(int(anime.last_ep), int(anime.info["Episodi"]) if anime.info["Episodi"].isdigit() else 0) # potenzialmente non numerico
        # Fetch episodes in chunks
        while start_range <= episode_count:
            end_range = min(start_range + 119, episode_count)
            search_url = f"{self.BASE_URL}/info_api/{anime.ref}/1"
            response = self.Client.get(
                url=search_url,
                params={
                    "start_range": start_range,
                    "end_range": end_range
                }
            )
            response.raise_for_status()
            episodi.update({str(episode['number']): str(episode['id']) for episode in response.json()['episodes']})
            start_range = end_range + 1
        return episodi

    def _episode_link(self, anime: Anime, episode: Anime.Episode) -> str:
        embed_url = f"{self.BASE_URL}/embed-url/{episode.ref}"
        response = self.Client.get(embed_url)
        response.raise_for_status()
        iframe_src = response.text.strip()

        # Fetch the video page
        video_response = self.Client.get(iframe_src)
        video_response.raise_for_status()

        # Usa una regex per estrarre il link video MP4 dallo script
        match = re.search(r"window.downloadUrl\s*=\s*'([^']*)", video_response.text)
        if not match:
            raise ValueError("Link video non trovato nella pagina")
        src_mp4 = match.group(1)
        return src_mp4

    def _info_anime(self, anime: Anime):
        if not anime.ref.isdigit():
            raise HTTPError("Errore 404: pagina non trovata")
        search_url = f"{self.BASE_URL}/info_api/{anime.ref}/"
        response = self.Client.get(search_url)
        response.raise_for_status()
        data = response.json()
        match data['status']:
            case "In Corso":
                anime.status = AnimeStatus.ONGOING
            case "Terminato":
                anime.status = AnimeStatus.FINISHED
            case "Non Rilasciato":
                anime.status = AnimeStatus.NOT_RELEASED
            case _:
                anime.status = AnimeStatus.UNKNOWN
        anime.last_ep = str(data['episodes_count'])
        anime.info["Genere"] = ', '.join(data['genres'])
        # anime.info["Correlati"] = data['related']

    def _parse_info(self, data: dict) -> tuple[str, str, int, AnimeStatus, dict[str, str]]:
        title = data['title_eng'] or data['title'] or data['title_it']
        last_ep = str(data['real_episodes_count']) if 'real_episodes_count' in data else "0" 
        anilist_id = data['anilist_id']
        match data['status']:
            case "In Corso":
                status = AnimeStatus.ONGOING
            case "Terminato":
                status = AnimeStatus.FINISHED
            case "Non Rilasciato":
                status = AnimeStatus.NOT_RELEASED
            case _:
                status = AnimeStatus.UNKNOWN
        info = {
            "Categoria": data['type'],
            "Audio": "Italiano" if data['dub'] else "??",
            "Data di Uscita": data['date'],
            "Stagione": data['season'],
            "Studio": data['studio'],
            "Voto": data['score'],
            "Durata": f"{data['episodes_length']} min", # potrebbe non essere in minuti"
            "Episodi": str(data['episodes_count']) if data['episodes_count'] != 0 else "??",
            "Visualizzazioni": data['visite'],
            "Trama": data['plot'],
        }
        return title, last_ep, anilist_id, status, info
