from __future__ import annotations
from collections import defaultdict
import awcli.utilities as utilities


class Anime:
    """
    Classe che rappresenta un anime.

    Attributes:
        name (str): il nome dell'anime.
        url (str): l'URL della pagina dell'anime su AnimeWorld.  
        ep (int, optional):
        ep_totali (str, optional): il numero reale di episodi totali dell'anime.
    """ 

    def __init__(self, name, url, ep=0, ep_totali="") -> None:
        self.name = name
        self.url = url
        self.ep_corrente = ep-1
        self.progress = defaultdict(int)
        self.ep = ep
        self.ep_totali = ep_totali
        self.ep_ini = 1
        self.url_episodi = list[Episode]

    def _set_episodes(self, episodi: list[str]) -> None:
        """
        Imposta i riferienti degli episodi dell'anime.
        Args:
            episodi (list[str]): lista dei riferimeti delgli episodi dell'anime (URL/ID).
        """
        self.url_episodi = [Episode(self, num, ref) for num, ref in enumerate(episodi)]
        self.ep = len(episodi)
        
    def _set_info(self, anilist_id, info: dict[str:str]) -> None:
        """
        Imposta le informazioni dell'anime.
        Args:
            anilist_id (int): l'ID di Anilist dell'anime.
            infos (list): lista delle informazioni dell'anime.
        """ 
        self.id_anilist = anilist_id
        self.info = info
        self.ep_totali = info["Episodi"]
        self.status = int(info["Stato"])
    
    def print_info(self):
        """
        Stampa le informazioni dell'anime.
        """
        utilities.my_print(self.name, cls=True)
        utilities.my_print("Categoria: ", end="", color="azzurro")
        utilities.my_print(self.info["Categoria"], format=0)
        utilities.my_print("Audio: ", end="", color="azzurro")
        utilities.my_print(self.info["Audio"], format=0)
        utilities.my_print("Data di Uscita: ", end="", color="azzurro")
        utilities.my_print(self.info["Data di Uscita"], format=0)
        utilities.my_print("Stagione: ", end="", color="azzurro")
        utilities.my_print(self.info["Stagione"], format=0)
        utilities.my_print("Studios: ", end="", color="azzurro")
        utilities.my_print(self.info["Studio"], format=0)
        utilities.my_print("Generi: ", end="", color="azzurro")
        utilities.my_print(self.info["Genere"], format=0)
        utilities.my_print("Voto medio: ", end="", color="azzurro")
        utilities.my_print(self.info["Voto"], format=0)
        utilities.my_print("Durata: ", end="", color="azzurro")
        utilities.my_print(self.info["Durata"], format=0)
        utilities.my_print("Episodi: ", end="", color="azzurro")
        utilities.my_print(self.info["Episodi"], format=0)
        utilities.my_print("Stato: ", end="", color="azzurro")
        match self.status:
            case 0:
                utilities.my_print("In corso", format=0)
            case 1:
                utilities.my_print("Finito", format=0)
            case 2:
                utilities.my_print("Non rilasciato", format=0)
        utilities.my_print("Visualizzazioni: ", end="", color="azzurro")
        utilities.my_print(self.info["Visualizzazioni"], format=0)
        utilities.my_print("Trama: ", end="", color="azzurro")
        utilities.my_print(self.info["Trama"], end="\n\n", format=0)

class Episode:
    """
    Classe che rappresenta un episodio di un anime.

    Attributes:
        num (str): il numero dell'episodio.
        ref (str): il riferimento dell'episodio.
    """
    def __init__(self, anime, num: str, ref: str) -> None:
        self._anime = anime
        self.num = num
        self.ref = ref

    def __str__(self) -> str:
        return f"{self._anime.name} Ep. {self.num}"