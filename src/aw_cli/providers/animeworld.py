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
        Gestisce cookie JavaScript (document.cookie) e imposta il csrf-token se presente.
        """
        if not re.match(r"^https?://", url):
            raise HTTPError("Errore 404: pagina non trovata")

        response = self.Client.get(url)

        # Gestione cookie impostati tramite JavaScript (document.cookie)
        cookie_match = re.search(
            r'document\.cookie\s*?=\s*?"([^=]+)=([^";]+)', response.text
        )
        if cookie_match:
            name, value = cookie_match.groups()
            self.Client.cookies.set(name, value)
            response = self.Client.get(url)

        response.raise_for_status()

        # Estrai e aggiorna il csrf-token se presente nella pagina per le chiamate API
        csrf_token_match = re.search(
            r'<meta.*?id="csrf-token"\s*?content="(.*?)">', response.text
        )
        if csrf_token_match:
            self.Client.headers["csrf-token"] = csrf_token_match.group(1)

        if response.status_code != 200 or "Errore 404" in response.text:
            raise HTTPError("Errore 404: pagina non trovata")

        return response.text

    def _search(self, input: str) -> list[Anime]:
        # Assicuriamoci che il client abbia cookies/csrf-token caricando prima la homepage
        if "csrf-token" not in self.Client.headers:
            try:
                self._get_html(self.BASE_URL)
            except Exception:
                pass

        response = self.Client.post(
            f"{self.BASE_URL}/api/search/v2", params={"keyword": input}
        )
        response.raise_for_status()

        data = response.json()
        if "error" in data or "animes" not in data:
            return []

        animes = []
        for elem in data["animes"]:
            link = elem.get("link")
            identifier = elem.get("identifier")
            if link and identifier:
                url = f"{self.BASE_URL}/play/{link}.{identifier}"
            else:
                url = self.BASE_URL

            name = elem.get("name", "")
            anime = Anime(unescape(name), url)

            # Pre-populate all metadata from search JSON using a clean helper
            anilist_id, status, info = self._parse_info(elem)
            anime.set_info(anilist_id, status, info)
            animes.append(anime)
        return animes

    def _latest(self, filter: str, specials: bool) -> list[Anime]:
        html = self._get_html(self.BASE_URL)
        animes = list[Anime]()

        # Trova tutti i tag <a> con classe "poster" per estrarre in modo robusto
        for a_tag in re.findall(r'<a\s+[^>]*class="poster"[^>]*>', html):
            href_match = re.search(r'href="([^"]+)"', a_tag)
            title_match = re.search(r'title="([^"]+)"', a_tag)
            if not href_match or not title_match:
                continue

            url = href_match.group(1)
            title = title_match.group(1)

            # Estrae l'episodio dal titolo (es: "Nome Anime Ep 9")
            ep = "0"
            ep_match = re.search(r' Ep[\.\s]+([^"]+)$', title)
            if ep_match:
                ep = ep_match.group(1).strip()
                name = title[: ep_match.start()].strip()
            else:
                name = title

            parts = url.strip("/").split("/")
            if len(parts) >= 3:
                anime_slug = parts[1]
                player_id = parts[2]
                anime_ref = f"{self.BASE_URL}/play/{anime_slug}"
                ep_ref = player_id
            else:
                anime_ref = self.BASE_URL + url
                ep_ref = self.BASE_URL + url

            anime = Anime(unescape(name), anime_ref, ep)
            anime.update_episodes({ep: ep_ref}, specials=specials)
            animes.append(anime)

        BLOCK_SIZE = 45
        filter_keys = ["a", "s", "d", "t"]
        multiplier = filter_keys.index(filter[0])

        start = multiplier * BLOCK_SIZE
        end = (multiplier + 1) * BLOCK_SIZE if multiplier < len(filter_keys) else None

        return animes[start:end]

    def _episodes(self, anime: Anime):
        html = self._get_html(anime.ref)
        episodes_url = dict[str, str]()

        # Estrae i tag <a> in modo super stabile limitandosi agli elementi con classe "episode"
        for a_tag in re.findall(r'<li class="episode">[\s\n]*(<a\s+[^>]+>)', html):
            id_match = re.search(r'data-id="([^"]+)"', a_tag)
            num_match = re.search(r'data-num="([^"]+)"', a_tag)
            if id_match and num_match:
                episodes_url[num_match.group(1)] = id_match.group(1)
        return episodes_url

    def _episode_link(self, anime: Anime, episode: Anime.Episode) -> str:
        player_id = episode.ref
        if "play/" in player_id:
            player_id = player_id.split("/")[-1]

        api_url = f"{self.BASE_URL}/api/episode/serverPlayerAnimeWorld?id={player_id}"
        response = self.Client.get(api_url)
        response.raise_for_status()

        source_match = re.search(r'<source src="([^"]+)"', response.text)
        if not source_match:
            raise ValueError("Errore nel parsing della pagina dell'episodio")
        return source_match.group(1)

    def _info_anime(self, anime: Anime):
        html = self._get_html(anime.ref)

        res = re.search(r'<a.*id="anilist-button".*href="\D*(\d*)"', html)
        anilist_id = int(res.group(1)) if res else 0

        temp = re.findall(
            r'<dt>(.*?):</dt>[\n\s]*<dd(?: class="[^"]*")?>((?:.|\n)+?)</dd>', html
        )
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
            value = re.sub(r"[\s\n]+", " ", re.sub(r"<.*?>", "", value)).strip()
            info[key] = unescape(value)

        anime.set_info(anilist_id, status, info)

    def _parse_info(self, elem: dict) -> tuple[int, AnimeStatus, dict[str, str]]:
        """Estrae e mappa i metadati ritornati dal JSON dell'API di ricerca di AnimeWorld."""
        anilist_id = elem.get("anilistId", 0)
        state_val = elem.get("stateName", "Sconosciuto")
        status = AnimeStatus.UNKNOWN
        if state_val == "Finito":
            status = AnimeStatus.FINISHED
        elif state_val == "In corso":
            status = AnimeStatus.ONGOING
        elif state_val == "Non rilasciato":
            status = AnimeStatus.NOT_RELEASED

        info = {
            "Categoria": "Anime" if elem.get("animeType") == "0" else "Movie",
            "Audio": "Italiano" if elem.get("dub") == "1" else "Giapponese",
            "Data di Uscita": elem.get("release") or elem.get("year", ""),
            "Studio": elem.get("studio", ""),
            "Genere": ", ".join(
                cat.get("name", "") for cat in elem.get("categories", [])
            ),
            "Voto": f"{elem.get('malVote')}" if elem.get("malVote") else "Sconosciuto",
            "Episodi": f"{elem.get('episodes', '0')}",
            "Stato": state_val,
            "Trama": elem.get("story", ""),
        }
        return int(anilist_id) if anilist_id else 0, status, info
