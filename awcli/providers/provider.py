import requests
from abc import ABC, abstractmethod
from awcli.anime import Anime, Episode
import awcli.utilities as ut


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
        self._session = requests.Session()
        self._session.headers = { 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'}

    def search(self, input: str) -> list[Anime]:
        """
        Ricerca un anime in base al titolo.
        
        Args:
            input (str): il titolo dell'anime da ricercare.

        Returns:
            list[Anime]: la lista degli anime trovati.
        """
        ut.my_print("Ricerco...", color="giallo")
        try:
            res = self._search(input)
            for anime in res:
                if ut.nome_os == "Android":
                    forbidden_char = '"*/:<>?\|'
                    replace_char = '”⁎∕꞉‹›︖＼⏐'
                    for a, b in zip(forbidden_char, replace_char):
                        anime.name = anime.name.replace(a, b)
            return res
        except Exception as e:
            ut.my_print(f"Errore nella ricerca: {e}", color="rosso")
            return []

    @abstractmethod
    def _search(self, input: str) -> list[Anime]:
        """
        Ricerca un anime in base al titolo.
        
        Args:
            input (str): il titolo dell'anime da ricercare.

        Returns:
            list[Anime]: la lista degli anime trovati.
        """

    def latest(self, filter: str = "all") -> list[Anime]:
        """
        Restituisce le ultime uscite degli anime.

        Args:
            filter (str, optional): permette di filtrare i risultati tra [all, dub, sub]. Default: all.

        Returns:
            list[Anime]: la lista degli anime trovati.
        """
        try:
            return self._latest(filter, ut.configData["general"]["specials"])
        except Exception as e:
            ut.my_print(f"Errore nel recupero delle ultime uscite: {e}", color="rosso")
            return []

    @abstractmethod
    def _latest(self, filter: str, specials: bool) -> list[Anime]:
        """
        Restituisce le ultime uscite degli anime.

        Args:
            filter (str): il filtro da applicare.

        Returns:
            list[Anime]: la lista degli anime trovati.
        """

    def episodes(self, anime: Anime):
        """
        Ottiene i riferimenti agli episodi disponibili dell'anime,
        caricandole dentro `anime` che viene modificato di conseguenza.

        Args:
            anime (Anime): l'anime di riferimento.
        """
        try:
            anime._update_episodes(
                self._episodes(anime), 
                ut.configData["general"]["specials"]
            )
        except requests.exceptions.HTTPError:
            ut.my_print("Il link è stato cambiato", color="rosso", end="\n")
            anime.url = self._search(anime.name)[0].url
            self.episodes(anime)
        except Exception as e:
            ut.my_print(f"Errore nel recupero degli episodi: {e}", color="rosso")

    @abstractmethod
    def _episodes(self, anime: Anime) -> dict[str, str]:
        """
        Ottiene i riferimenti agli episodi disponibili dell'anime.

        Args:
            anime (Anime): l'anime di riferimento.

        Returns:
            dict[str, str]: dizionario dei riferimenti degli episodi dell'anime (numero->URL/ID).
        """

    def episode_link(self, episode: Episode) -> str:
        """
        Cerca il link del video dell'episodio. 

        Args:
            episode (Episode): l'episodio di riferimento.

        Returns:
            str: il link.
        """
        try:
            return self._episode_link(episode)
        except requests.exceptions.HTTPError:
            self.episodes(episode._anime)
            return self.episode_link(episode._anime.episode(episode.num))  # Retry with the new URL
        except Exception as e:
            ut.my_print(f"Errore nel recupero del link dell'episodio: {e}", color="rosso")

    @abstractmethod
    def _episode_link(self, episode: Episode) -> str:
        """
        Cerca il link del video dell'episodio. 

        Args:
            episode (Episode): l'episodio di riferimento.

        Returns:
            str: il link.
        """
    
    def info_anime(self, anime: Anime):
        """
        Prende le informazioni dell'anime selezionato,
        caricandole dentro `anime` che viene modificato di conseguenza.
        
        Args:
            anime (Anime): l'anime di riferimento.
        """
        try:
            return self._info_anime(anime)
        except requests.exceptions.HTTPError:
            ut.my_print("Il link è stato cambiato", color="rosso", end="\n")
            anime.url = self._search(anime.name)[0].url
            self._info_anime(anime)
        except Exception as e:
            ut.my_print(f"Errore nel recupero delle informazioni dell'anime: {e}", color="rosso")
            return {}

    @abstractmethod
    def _info_anime(self, anime: Anime) -> dict:
        """
        Prende le informazioni dell'anime selezionato.

        Args:
            anime (Anime): l'anime di riferimento.

        Returns:
            dict: le informazioni dell'anime.
        """