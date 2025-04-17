from abc import ABC
from awcli.anime import Anime

class Provider(ABC):
    """
    Classe astratta che rappresenta un generico Provider.
    """

    def search(input: str) -> list[Anime]:
        """
        Ricerca un anime in base al titolo.
        
        Args:
            input (str): il titolo dell'anime da ricercare.

        Returns:
        list[Anime]: la lista degli anime trovati.
        """

    def latest(filter = "all") -> list[Anime]:
        """
        Restituisce le ultime uscite degli anime.

        Args:
            filter (str, optional): permette di filtrare i risultati tra [all, dub, sub]. Default: all.

        Returns:
            list[Anime]: la lista degli anime trovati.
        """
    
    def episode_link(anime: Anime, ep: int) -> str:
        """
        Cerca il link del video dell'episodio. 

        Args:
            anime (Anime): l'anime di riferimento. 
            ep (int): l'episodio scelto.

        Returns:
            str: il link.
        """
    
    def info_anime(anime: Anime):
        """
        Prende le informazioni dell'anime selezionato,
        caricandole dentro `anime` che viene modificato di conseguenza.
        
        Args:
            anime (Anime): l'anime di riferimento.
        """

    def episodes(anime: Anime):
        """
        Ottiene i riferimenti agli episodi disponibili dell'anime,
        caricandole dentro `anime` che viene modificato di conseguenza.

        Args:
            anime (Anime): l'anime di riferimento.
        """