from __future__ import annotations
from enum import Enum
from functools import total_ordering
import awcli.utilities as ut


class AnimeStatus(Enum):
    """Enum for anime status, maintaining the original order."""
    ONGOING = (0, "In corso")
    FINISHED = (1, "Finito") 
    NOT_RELEASED = (2, "Non rilasciato")
    UNKNOWN = (-1, "Sconosciuto")
    
    def __init__(self, code: int, display_name: str):
        self.code = code
        self.display_name = display_name

class Anime:
    """
    Classe che rappresenta un anime.

    Attributes:
        name (str): il nome dell'anime.
        ref (str): il riferimento dell'anime.
        curr_ep (str): l'episodio corrente.
        last_ep (str): l'ultimo episodio disponibile.
        id_anilist (int): l'ID dell'anime su Anilist.
        info (dict[str, str]): dizionario con le informazioni dell'anime.
    """ 

    def __init__(self, name: str, ref: str, curr_ep: str = "0", last_ep: str = "0", status: AnimeStatus = AnimeStatus.UNKNOWN) -> None:
        self.name: str = name
        self.ref: str = ref
        self.id_anilist: int = 0
        self.curr_ep: str = curr_ep
        self.last_ep: str = last_ep if last_ep != "0" else curr_ep
        self.status: AnimeStatus = status
        self._episodes: list[Anime.Episode] = []
        self._num_to_index: dict[str, int] = {}
        self.info: dict[str, str] = {}

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Anime):
            return False

        if self.id_anilist and other.id_anilist:
            return self.id_anilist == other.id_anilist
        
        return self.name == other.name # idealmente andrebbe tolto

    def __hash__(self) -> int:
        if self.id_anilist:
            return hash(self.id_anilist)
        
        return hash(self.name)

    def update_episodes(self, episodes: dict[str, str], specials: bool = True) -> None:
        """
        Imposta i riferimenti degli episodi dell'anime.
        Args:
            episodi (dict[str, str]): dizionario dei riferimenti degli episodi dell'anime (numero->URL/ID).
        """
        for num, ref in episodes.items():
            if not specials and ("." in num or num == "0"):
                continue
            if (ep := self.episode(num)):
                ep.ref = ref
                continue
            self._episodes.append(Anime.Episode(self, num, ref))

        self._episodes.sort()
        self._num_to_index = {ep.num: i for i, ep in enumerate(self._episodes)}

        if len(self._episodes) > 0 and self._episodes[-1] > self.episode(self.last_ep):
            self.last_ep = self._episodes[-1].num

    def episodes(self) -> list[str]:
        """
        Restituisce una lista dei numeri degli episodi disponibili.
        """
        return list(self._num_to_index.keys())

    def episode(self, ep_num: str) -> Anime.Episode | None:
        """
        Restituisce il riferimento dell'episodio corrispondente al numero specificato.
        Args:
            ep (str): Il numero dell'episodio.
        Returns:
            (Anime.Episode | None): l'episodio corrispondente al numero,
                 oppure None se non è presente.
        """

        if ep_num not in self._num_to_index:
            return None

        return self._episodes[self._num_to_index[ep_num]]

    def set_info(self, anilist_id: int, status: AnimeStatus, info: dict[str, str]) -> None:
        """
        Imposta le informazioni dell'anime.
        Args:
            anilist_id (int): l'ID di Anilist dell'anime.
            infos (list): lista delle informazioni dell'anime.
        """ 
        self.id_anilist = anilist_id
        self.info = info
        self.status = status
    
    def print_info(self):
        """
        Stampa le informazioni dell'anime.
        """
        ut.my_print(self.name, cls=True)
        tmp_info = dict(self.info)

        # Usa l'enum per lo stato
        tmp_info["Stato"] = self.status.display_name

        tmp_info["Trama"] = tmp_info.pop("Trama")

        for key, value in tmp_info.items():
            ut.my_print(f"{key}: ", end="", color="azzurro")
            ut.my_print(value, format=0)

    def to_dict(self) -> dict[str, object]:
        """
        Restituisce un dizionario con le informazioni dell'anime.

        Returns:
            dict: un dizionario con le informazioni dell'anime.
        """
        return {
            "name": self.name,
            "ref": self.ref,
            "curr_ep": self.curr_ep,
            "last_ep": self.last_ep,
            "id_anilist": self.id_anilist,
            "status": self.status.code,
            "info": self.info,
            "episodes": [ep.to_dict() for ep in self._episodes]
        }
    
    @total_ordering
    class Episode:
        """
        Classe che rappresenta un episodio di un anime.

        Attributes:
            num (str): il numero dell'episodio.
            ref (str): il riferimento dell'episodio.
            progress (int): il progresso di visualizzazione dell'episodio.
            completed (bool): indica se l'episodio è stato completato.
        """

        ## TODO: fare un comparatore in base a num (considerando i casi x, x.5, x-y)

        def __init__(self, anime: Anime, num: str, ref: str) -> None:
            self._anime = anime
            self.num = num
            self.ref = ref
            self.progress = 0
            self.completed = False

        def __str__(self) -> str:
            return f"{self._anime.name} Ep. {self.num}"

        def __repr__(self) -> str:
            return f"Episode(num={self.num}, ref={self.ref}, progress={self.progress}, completed={self.completed})"

        def __eq__(self, other: object) -> bool:
            if not isinstance(other, Anime.Episode):
                return False
            return self._anime == other._anime and self.num == other.num

        def __hash__(self) -> int:
            return hash((self._anime, self.num))

        def __lt__(self, other: object) -> bool:
            if not isinstance(other, Anime.Episode) or self._anime != other._anime:
                return False
            self_num = self.numeric() if '-' in self.num else float(self.num)
            other_num = other.numeric() if '-' in other.num else float(other.num)
            return self_num < other_num

        def next(self) -> Anime.Episode | None:
            """
            Restituisce l'episodio successivo.

            Returns:
                (Anime.Episode | None): l'episodio successivo, oppure None se non esiste.
            """
            index = self._anime._num_to_index[self.num]+1
            if index >= len(self._anime._episodes):
                return None
            return self._anime._episodes[index]

        def prev(self) -> Anime.Episode | None:
            """
            Restituisce l'episodio precedente.

            Returns:
                (Anime.Episode | None): l'episodio precedente, oppure None se non esiste.
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

        def to_dict(self) -> dict[str, object]:
            """
            Restituisce un dizionario con le informazioni dell'episodio.
            """
            return {
                "num": self.num,
                "ref": self.ref,
                "progress": self.progress,
                "completed": self.completed
        }


def numeric(num: str) -> int:
    if '.' in num:
        return int(num.split('.')[0])
    if '-' in num:
        return int(num.split('-')[1])
    return int(num)