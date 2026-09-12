import re
import base64
import xml.etree.ElementTree as ET
from html import unescape
from ..anime import Anime, AnimeStatus
from .provider import Provider


class Animesaturn(Provider):
    """
    Classe che gestisce il collegamento con AnimeSaturn.

    Riferimenti usati:
        - anime.ref: lo slug dell'anime con l'ID finale (es. "naruto-iN621").
        - episode.ref: l'URL della pagina del player (es. ".../anime/naruto-iN621/ep-1").
    """

    PLAYER_URL = "https://play.saturncdn.net"
    MAX_SEARCH_PAGES = 3

    def __init__(self, client=None):
        super().__init__("https://www.animesaturn.net", client=client)

    def _get_html(self, url: str, **kwargs) -> str:
        response = self.Client.get(url, **kwargs)
        response.raise_for_status()
        return response.text

    @staticmethod
    def _is_dub(slug: str) -> bool:
        """Le versioni doppiate hanno "-ita" prima dell'ID finale (es. "naruto-ita-ZSYWi")."""
        return re.search(r"-ita-[A-Za-z0-9]+$", slug) is not None

    @staticmethod
    def _decode(b64: str, key: str) -> str:
        """Replica la funzione dec() della pagina embed: base64 + XOR con il token."""
        raw = base64.b64decode(b64)
        return "".join(chr(byte ^ ord(key[i % len(key)])) for i, byte in enumerate(raw))

    def _search(self, input: str) -> list[Anime]:
        url: str | None = f"{self.BASE_URL}/filter"
        params: dict[str, str] | None = {"key": input}
        animes = dict[str, Anime]()

        # i risultati sono paginati (30 per pagina): si segue il link rel="next"
        # fino a un massimo di pagine, per non fare troppe richieste al sito
        for _ in range(self.MAX_SEARCH_PAGES):
            if url is None:
                break
            html = self._get_html(url, params=params)

            # solo le card dei risultati: le sezioni laterali usano un markup diverso
            for match in re.finditer(r'<a href="/anime/([^"]+)" class="ac group">(.*?)</a>', html, re.S):
                slug, card = match.groups()
                title = re.search(r'<h3 class="ac__title">([^<]+)</h3>', card)
                if not title or slug in animes:
                    continue
                sub = re.search(r'<p class="ac__sub">([^<]*)</p>', card)
                eps = re.search(r"(\d+)\s*ep", sub.group(1)) if sub else None
                animes[slug] = Anime(unescape(title.group(1).strip()), slug, last_ep=eps.group(1) if eps else "0")

            next_page = re.search(r'<a href="([^"]+)"[^>]*rel="next"', html)
            url = self.BASE_URL + unescape(next_page.group(1)) if next_page else None
            params = None  # il link della pagina successiva contiene già la query

        return list(animes.values())

    def _latest(self, filter: str, specials: bool) -> list[Anime]:
        # il feed RSS è più stabile dell'HTML della homepage
        # TODO: il filtro "t" (tendenze) non ha un equivalente diretto, per ora mostra tutto
        xml = self._get_html(f"{self.BASE_URL}/rss/episodes")
        animes = list[Anime]()

        for item in ET.fromstring(xml).iter("item"):
            link = item.findtext("link") or ""
            match = re.search(r"/episode/([^/]+)/ep-([\w.]+)", link)
            if not match:
                continue
            slug, num = match.groups()
            dub = self._is_dub(slug)
            if (filter == "d" and not dub) or (filter == "s" and dub):
                continue

            name = unescape(item.findtext("category") or item.findtext("title") or slug)
            if dub and "(ITA)" not in name:
                name += " (ITA)"

            anime = Anime(name, slug, curr_ep=num)
            anime.update_episodes({num: f"{self.BASE_URL}/anime/{slug}/ep-{num}"}, specials=specials)
            animes.append(anime)

        return animes

    def _episodes(self, anime: Anime) -> dict[str, str]:
        html = self._get_html(f"{self.BASE_URL}/anime/{anime.ref}")
        episodes = dict[str, str]()

        # la pagina contiene anche i pulsanti "primo/ultimo episodio": i duplicati si eliminano da soli
        for num in re.findall(rf"/episode/{re.escape(anime.ref)}/ep-([\w.]+)\"", html):
            episodes[num] = f"{self.BASE_URL}/anime/{anime.ref}/ep-{num}"

        return dict(sorted(episodes.items(), key=lambda kv: float(kv[0]) if kv[0].replace(".", "", 1).isdigit() else 0))

    def _episode_link(self, anime: Anime, episode: Anime.Episode) -> str:
        # 1) pagina del player -> iframe dell'embed
        html = self._get_html(episode.ref)
        iframe = re.search(r'<iframe[^>]*id="watch-iframe"[^>]*>', html)
        src = re.search(r'src="([^"]+)"', iframe.group(0)) if iframe else None
        if not src:
            raise ValueError("Iframe del player non trovato")
        embed_url = unescape(src.group(1))

        # 2) pagina embed -> window.__E = {i: id, k: token, e: scadenza}
        embed = self._get_html(embed_url, headers={"Referer": f"{self.BASE_URL}/"})
        data = re.search(r'window\.__E\s*=\s*\{i:(\d+),k:"([^"]+)",e:(\d+)\}', embed)
        if not data:
            raise ValueError("Dati del player non trovati nella pagina embed")
        video_id, token, expires = data.groups()

        # 3) playlist -> JSON con la sorgente offuscata nel campo "d"
        response = self.Client.get(
            f"{self.PLAYER_URL}/embed/{video_id}/playlist",
            params={"token": token, "expires": expires},
            headers={"Referer": embed_url},
        )
        response.raise_for_status()
        source = self._decode(response.json()["d"], token)

        # alcuni episodi sono ospitati su YouTube (mpv li apre tramite yt-dlp)
        if source.startswith("youtube/"):
            return f"https://www.youtube.com/watch?v={source[len('youtube/'):]}"
        if not source.startswith("http"):
            raise ValueError("Sorgente video non valida")
        return source

    @staticmethod
    def _clean(html: str) -> str:
        """Rimuove i tag HTML, decodifica le entità e compatta gli spazi."""
        text = re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", html))).strip()
        return text.replace("( ", "(").replace(" )", ")")

    def _info_anime(self, anime: Anime) -> None:
        html = self._get_html(f"{self.BASE_URL}/anime/{anime.ref}")

        res = re.search(r"https?://anilist\.co/anime/(\d+)", html)
        anilist_id = int(res.group(1)) if res else 0

        # righe della scheda: <span class="... uppercase tracking-wider">Etichetta</span> seguita dal valore
        info = dict[str, str]()
        rows = re.findall(r'<span class="[^"]*uppercase tracking-wider[^"]*">([^<]+)</span>(.*?)</(?:a|div)>', html, re.S)
        for label, value in rows:
            info[label.strip()] = self._clean(value)

        genres = re.search(r'<div class="ag-genres[^"]*">(.*?)</div>', html, re.S)
        if genres:
            info["Genere"] = ", ".join(self._clean(g) for g in re.findall(r'<a[^>]*class="chip"[^>]*>(.*?)</a>', genres.group(1), re.S))

        plot = re.search(r'<section class="ag-story"[^>]*>.*?</h2>\s*<div[^>]*>(.*?)</div>', html, re.S)
        if plot:
            info["Trama"] = self._clean(plot.group(1))

        # aw-cli riconosce il doppiaggio da info["Audio"] e mostra info["Episodi"] nei menu
        lingua = info.pop("Lingua", "")
        dub = self._is_dub(anime.ref) or lingua.lower() == "italiano"
        info["Audio"] = "Italiano" if dub else (lingua or "Giapponese")
        info.setdefault("Episodi", anime.last_ep)

        anime.set_info(anilist_id, AnimeStatus.from_string(info.get("Stato", "")), info)
