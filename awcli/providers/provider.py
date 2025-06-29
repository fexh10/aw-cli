from abc import ABC, abstractmethod
from awcli.anime import Anime

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
        self._url = url
        self._headers = { 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'}

    @abstractmethod
    def search(input: str) -> list[Anime]:
        """
        Ricerca un anime in base al titolo.
        
        Args:
            input (str): il titolo dell'anime da ricercare.

        Returns:
            list[Anime]: la lista degli anime trovati.
        """

    @abstractmethod
    def latest(filter = "all") -> list[Anime]:
        """
        Restituisce le ultime uscite degli anime.

        Args:
            filter (str, optional): permette di filtrare i risultati tra [all, dub, sub]. Default: all.

        Returns:
            list[Anime]: la lista degli anime trovati.
        """
    
    @abstractmethod
    def episodes(anime: Anime):
        """
        Ottiene i riferimenti agli episodi disponibili dell'anime,
        caricandole dentro `anime` che viene modificato di conseguenza.

        Args:
            anime (Anime): l'anime di riferimento.
        """

    @abstractmethod
    def episode_link(anime: Anime, ep: int) -> str:
        """
        Cerca il link del video dell'episodio. 

        Args:
            anime (Anime): l'anime di riferimento. 
            ep (int): l'episodio scelto.

        Returns:
            str: il link.
        """
    
    @abstractmethod
    def info_anime(anime: Anime):
        """
        Prende le informazioni dell'anime selezionato,
        caricandole dentro `anime` che viene modificato di conseguenza.
        
        Args:
            anime (Anime): l'anime di riferimento.
        """