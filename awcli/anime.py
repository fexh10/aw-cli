from __future__ import annotations
import awcli.utilities as utilities

class Anime:
    """
    Classe che rappresenta un anime.

    Attributes:
        name (str): il nome dell'anime.
        url (str): l'URL della pagina dell'anime su AnimeWorld.  
        ep (str, optional):.
    """ 

    def __init__(self, name, url, curr_ep="0", last_ep="0") -> None:
        self.name = name
        self.url = url
        self.curr_ep = curr_ep
        self.last_ep = last_ep if last_ep != "0" else curr_ep
        self._episodes = list[Episode]()
        self._num_to_index = dict[str, int]()

    def __eq__(self, other):
        if not isinstance(other, Anime):
            return NotImplemented
        
        if self.id_anilist:
            return self.id_anilist == other.id_anilist
        
        return self.name == other.name

    def __hash__(self):
        if self.id_anilist:
            return hash(self.id_anilist)
        
        return hash(self.name)

    def _set_episodes(self, episode: dict[str, str], specials: bool = True) -> None:
        """
        Imposta i riferimenti degli episodi dell'anime.
        Args:
            episodi (dict[str, str]): dizionario dei riferimenti degli episodi dell'anime (numero->URL/ID).
        """
        
        self._episodes = []
        self._num_to_index = dict[str, int]()
        for num, ref in episode.items():
            if not specials and ("." in num or num == "0"):
                continue
            self._episodes.append(Episode(self, num, ref))
            self._num_to_index[num] = len(self._episodes) - 1

        if len(self._episodes) > 0 and self._episodes[-1].numeric() > numeric(self.last_ep):
            self.last_ep = self._episodes[-1].num

    def episodes(self) -> list[str]:
        """
        Restituisce una lista dei numeri degli episodi disponibili.
        """
        return list(self._num_to_index.keys())

    def episode(self, ep_num: str) -> Episode | None:
        """
        Restituisce il riferimento dell'episodio corrispondente al numero specificato.
        Args:
            ep (str): Il numero dell'episodio.
        Returns:
            (Episode | None): l'episodio corrispondente al numero,
                 oppure None se non è presente.
        """

        if ep_num not in self._num_to_index:
            return None

        return self._episodes[self._num_to_index[ep_num]]

    def _set_info(self, anilist_id, info: dict[str:str]) -> None:
        """
        Imposta le informazioni dell'anime.
        Args:
            anilist_id (int): l'ID di Anilist dell'anime.
            infos (list): lista delle informazioni dell'anime.
        """ 
        self.id_anilist = anilist_id
        self.info = info
    
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
        match self.info["Stato"]:
            case "0":
                utilities.my_print("In corso", format=0)
            case "1":
                utilities.my_print("Finito", format=0)
            case "2":
                utilities.my_print("Non rilasciato", format=0)
        utilities.my_print("Visualizzazioni: ", end="", color="azzurro")
        utilities.my_print(self.info["Visualizzazioni"], format=0)
        utilities.my_print("Trama: ", end="", color="azzurro")
        utilities.my_print(self.info["Trama"], end="\n\n", format=0)

    def to_dict(self) -> dict:
        """
        Restituisce un dizionario con le informazioni dell'anime.

        Returns:
            dict: un dizionario con le informazioni dell'anime.
        """
        return {
            "name": self.name,
            "url": self.url,
            "curr_ep": self.curr_ep,
            "last_ep": self.last_ep,
            "id_anilist": self.id_anilist,
            "info": self.info,
            "episodes": [ep.to_dict() for ep in self._episodes]
        }

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
        self.progress = 0
        self.completed = False

    def __str__(self) -> str:
        return f"{self._anime.name} Ep. {self.num}"

    def next(self) -> Episode | None:
        """
        Restituisce l'episodio successivo.

        Returns:
            (Episode | None): l'episodio successivo, oppure None se non esiste.
        """
        index = self._anime._num_to_index[self.num]+1
        if index >= len(self._anime._episodes):
            return None
        return self._anime._episodes[index]

    def prev(self) -> Episode | None:
        """
        Restituisce l'episodio precedente.

        Returns:
            (Episode | None): l'episodio precedente, oppure None se non esiste.
        """
        index = self._anime._num_to_index[self.num]-1
        if index < 0:
            return None
        return self._anime._episodes[index]
    
    def numeric(self) -> int:
        """
        Restituisce il numero dell'episodio come intero.

        - se è x.5 arrotonda a x.
        - se è x-y restituisce y.

        Returns:
            int: il numero dell'episodio.
        """
        return numeric(self.num)

    def is_completed(self) -> bool:
        """
        Check if the episode is completed.
        """
        return self.progress == 0 and self.completed

    def set_progress(self, progress: int) -> None:
        """
        Imposta il progresso dell'episodio.
        """
        self.progress = progress
        if progress != 0:
            self.completed = False

    def mark_completed(self) -> None:
        """
        Segna l'episodio come completato.
        """
        self.progress = 0
        self.completed = True

    def to_dict(self) -> dict:
        """
        Restituisce un dizionario con le informazioni dell'episodio.
        """
        return {
            "num": self.num,
            "ref": self.ref,
            "progress": self.progress,
            "completed": self.completed
        }


def numeric(num) -> int:
    if '.' in num:
        return int(num.split('.')[0])
    if '-' in num:
        return int(num.split('-')[1])
    return int(num)

if __name__ == "__main__":
    anime = Anime("Test", "test", "1", "12")
    anime._set_episodes({"1": "ref1", "2": "ref2"})
    anime._set_info(12345, {"Episodi": "12", "Stato": "1"})
    print(anime.to_dict())