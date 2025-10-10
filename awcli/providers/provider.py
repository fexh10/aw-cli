from abc import ABC, abstractmethod
from httpx import Client, AsyncClient, HTTPError
from awcli.anime import Anime, AnimeStatus
import awcli.utilities as ut

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
                ut.my_print(f"Errore {e.__class__.__name__} durante {func.__name__}: {e}", color="rosso")
                return None
        return wrapper
    return decorator

def update_link(self, callback, anime: Anime, episode: Anime.Episode | None = None):
    """
    Gestisce il caso in cui il riferimento dell'anime o all'episodio non è più valido
    """
    if episode:
        ut.my_print("Il link dell'episodio è stato cambiato", color="rosso", end="\n")
        self.episodes(anime)
        return callback(self, anime, anime.episode(episode.num))
    else:
        ut.my_print("Il link dell'anime è stato cambiato", color="rosso", end="\n")
        res: list[Anime] = self.search(anime.name)
        if len(res) == 0:
            raise LookupError(f"Nessun risultato trovato per {anime.name} su {self.__class__.__name__}")
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
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'
            },
            follow_redirects=True,
            timeout=10
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
        ut.my_print("Ricerco...", color="giallo")
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

        Args:
            filter (str, optional): permette di filtrare i risultati tra [all, dub, sub]. Default: all.

        Returns:
            list[Anime]: la lista degli anime trovati.
        """
        return self._latest(filter, ut.configData["general"]["specials"])

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
            self._episodes(anime), 
            ut.configData["general"]["specials"]
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
    
    @error_handler(relink=True)
    def info_anime(self, anime: Anime):
        """
        Prende le informazioni dell'anime selezionato,
        caricandole dentro `anime` che viene modificato di conseguenza.
        
        Args:
            anime (Anime): l'anime di riferimento.
        """
        self._info_anime(anime)

    @abstractmethod
    def _info_anime(self, anime: Anime) -> None:
        """
        Prende le informazioni dell'anime selezionato e le imposta dentro l'anime.

        Args:
            anime (Anime): l'anime di riferimento.
        """
