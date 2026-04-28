import hashlib
import json
import time
import urllib.request
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from httpx import Client, HTTPError  # , AsyncClient
from ..anime import Anime, AnimeStatus
from .. import utilities as ut


def error_handler(relink=False):
    """
    Decoratore per gestire gli errori delle funzioni.
    """

    def decorator(func):
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                if relink and isinstance(e, HTTPError):
                    return update_link(self, func, *args, **kwargs)
                ut.console.print(
                    f"Errore {e.__class__.__name__} durante {func.__name__}: {e}",
                    style="error",
                )
                return None

        return wrapper

    return decorator


def update_link(self, callback, anime: Anime, episode: Anime.Episode | None = None):
    """
    Gestisce il caso in cui il riferimento dell'anime o all'episodio non è più valido
    """
    if episode:
        ut.console.print("Il link dell'episodio è stato cambiato", style="error")
        self.episodes(anime)
        return callback(self, anime, anime.episode(episode.num))
    else:
        ut.console.print("Il link dell'anime è stato cambiato", style="warning")
        res: list[Anime] | None = self.search(anime.name)
        if not res:
            raise LookupError(
                f"Errore o nessun risultato durante la ricerca di {anime.name} su {self.__class__.__name__}"
            )
        anime.ref = res[0].ref
        return callback(self, anime)


class Provider(ABC):
    """
    Classe astratta che rappresenta un generico Provider.

    Attributes:
        _url (str): l'url del sito del provider.
        _headers (dict): gli headers da utilizzare per le richieste HTTP.
    """

    def __init__(self, url: str):
        """
        Costruisce un'instanza di Provider.

        Args:
            url (str): l'url del sito del provider.
        """
        self.BASE_URL = url
        self.Client = Client(
            headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
                "Connection": "close"
            },
            follow_redirects=True,
            timeout=10,
        )

    @error_handler(relink=False)
    def search(self, input: str) -> list[Anime]:
        """
        Ricerca un anime in base al titolo.

        Args:
            input (str): il titolo dell'anime da ricercare.

        Returns:
            list[Anime]: la lista degli anime trovati.
        """
        ut.console.print("Ricerco...", style="warning")
        res = self._search(input)
        for anime in res:
            anime.name = ut.sanitize_filename(anime.name)
        return res

    @abstractmethod
    def _search(self, input: str) -> list[Anime]:
        """
        Implementazione della search
        """

    @error_handler(relink=False)
    def latest(self, filter: str = "all") -> list[Anime]:
        """
        Restituisce le ultime uscite degli anime.
        Si assicura che tutte le entry di uno stesso anime abbiano gli stessi episodi.

        Args:
            filter (str, optional): permette di filtrare i risultati tra [all, dub, sub]. Default: all.

        Returns:
            list[Anime]: la lista degli anime trovati.
        """
        specials = ut.config_data["general"]["specials"]
        animes = self._latest(filter, specials)

        grouped_animes: dict[str, list[Anime]] = {}
        for anime in animes:
            grouped_animes.setdefault(anime.name, []).append(anime)

        for group in grouped_animes.values():
            if len(group) > 1:
                all_episodes = {}
                for anime in group:
                    for ep in anime._episodes:
                        all_episodes[ep.num] = ep.ref

                for anime in group:
                    anime.update_episodes(all_episodes, specials=specials)

        return animes

    @abstractmethod
    def _latest(self, filter: str, specials: bool) -> list[Anime]:
        """
        Implementazione della latest
        """

    @error_handler(relink=True)
    def episodes(self, anime: Anime):
        """
        Ottiene i riferimenti agli episodi disponibili dell'anime,
        caricandole dentro `anime` che viene modificato di conseguenza.

        Args:
            anime (Anime): l'anime di riferimento.
        """
        anime.update_episodes(
            self._episodes(anime), ut.config_data["general"]["specials"]
        )

    @abstractmethod
    def _episodes(self, anime: Anime) -> dict[str, str]:
        """
        Ottiene i riferimenti agli episodi disponibili dell'anime.

        Args:
            anime (Anime): l'anime di riferimento.

        Returns:
            dict[str, str]: dizionario dei riferimenti degli episodi dell'anime (numero->URL/ID).
        """

    @error_handler(relink=True)
    def episode_link(self, anime: Anime, episode: Anime.Episode) -> str:
        """
        Cerca il link del video dell'episodio.

        Args:
            episode (Anime.Episode): l'episodio di riferimento.

        Returns:
            str: il link.
        """
        return self._episode_link(anime, episode)

    @abstractmethod
    def _episode_link(self, anime: Anime, episode: Anime.Episode) -> str:
        """
        Implementazione della episode_link.
        """

    def _get_info_cache_dir(self) -> Path:
        """Ritorna la directory di cache per le info di questo provider."""
        cache_dir = Path.home() / ".cache" / "aw-cli" / "info" / self.__class__.__name__
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir

    def _get_image_cache_dir(self) -> Path:
        """Ritorna la directory di cache per le immagini."""
        cache_dir = Path.home() / ".cache" / "aw-cli" / "images"
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir

    def _cache_key(self, anime: Anime) -> str:
        """Genera una chiave di cache univoca basata sul ref dell'anime."""
        return hashlib.md5(anime.ref.encode()).hexdigest()

    def _image_name(self, anime: Anime, cover_url: str) -> str:
        """Ritorna un nome file univoco per l'immagine."""
        if anime.anilist_id:
            return f"{anime.anilist_id}.jpg"
        return f"{hashlib.md5(cover_url.encode()).hexdigest()}.jpg"

    @error_handler(relink=True)
    def info_anime(self, anime: Anime):
        """
        Prende le informazioni dell'anime selezionato,
        caricandole dentro `anime` che viene modificato di conseguenza.
        Utilizza una cache su disco per evitare richieste ripetute.

        Args:
            anime (Anime): l'anime di riferimento.
        """
        cache_dir = self._get_info_cache_dir()
        cache_file = cache_dir / f"{self._cache_key(anime)}.json"

        if cache_file.exists():
            try:
                data = json.loads(cache_file.read_text())
                status_str = data.get("status", "Sconosciuto")
                cached_at = data.get("cached_at", 0)

                # Check expiration based on cache configurations
                age_hours = (time.time() - cached_at) / 3600
                stale = False

                if status_str == "In corso":
                    if age_hours > ut.config_data.get("cache", {}).get("ttl_ongoing_hours", 1):
                        stale = True
                elif status_str in ["Non rilasciato", "Sconosciuto"]:
                    if age_hours > ut.config_data.get("cache", {}).get("ttl_unreleased_hours", 24):
                        stale = True
                elif status_str == "Terminato":
                    if age_hours > (ut.config_data.get("cache", {}).get("ttl_finished_days", 30) * 24):
                        stale = True

                if not stale:
                    old_cover = anime.info.get("Cover")
                    anime.set_info(
                        anilist_id=data["anilist_id"],
                        status=AnimeStatus.from_string(status_str),
                        info=data["info"],
                    )
                    if old_cover and "Cover" not in anime.info:
                        anime.info["Cover"] = old_cover
                    return
            except (json.JSONDecodeError, KeyError):
                pass

            # If we reach here, cache is stale or invalid
            cache_file.unlink(missing_ok=True)

        old_cover = anime.info.get("Cover")
        self._info_anime(anime)
        if old_cover and "Cover" not in anime.info:
            anime.info["Cover"] = old_cover

        # Salva in cache
        try:
            cache_data = {
                "anilist_id": anime.anilist_id,
                "status": anime.status.value,
                "cached_at": time.time(),
                "info": anime.info,
            }
            cache_file.write_text(json.dumps(cache_data, ensure_ascii=False))
        except Exception:
            pass

    def cover_image(self, anime: Anime) -> Optional[Path]:
        """
        Ritorna il path dell'immagine di copertina dell'anime.
        Se non è in cache, la scarica e la salva su disco.

        Args:
            anime (Anime): l'anime di riferimento.

        Returns:
            Optional[Path]: il path dell'immagine, o None se non disponibile.
        """
        cover_url = anime.info.get("Cover") if anime.info else None
        if not cover_url:
            return None

        cache_dir = self._get_image_cache_dir()
        img_path = cache_dir / self._image_name(anime, cover_url)

        if img_path.exists() and img_path.stat().st_size > 0:
            return img_path

        try:
            req = urllib.request.Request(cover_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                tmp_path = img_path.with_suffix('.tmp')
                tmp_path.write_bytes(response.read())
                tmp_path.rename(img_path)
            return img_path
        except Exception:
            return None

    @abstractmethod
    def _info_anime(self, anime: Anime) -> None:
        """
        Prende le informazioni dell'anime selezionato e le imposta dentro l'anime.

        Args:
            anime (Anime): l'anime di riferimento.
        """
