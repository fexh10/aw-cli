from __future__ import annotations
from enum import Enum
from functools import total_ordering
from rich.console import Console, ConsoleOptions, RenderResult
from rich.text import Text


class AnimeStatus(Enum):
    """Enum for anime status, maintaining the original order."""
    ONGOING = "In corso"
    FINISHED = "Finito"
    NOT_RELEASED = "Non rilasciato"
    UNKNOWN = "Sconosciuto"

    @classmethod
    def from_string(cls, status_str: str) -> AnimeStatus:
        match status_str:
            case "In corso":
                return cls.ONGOING
            case "Finito":
                return cls.FINISHED
            case "Non rilasciato":
                return cls.NOT_RELEASED
            case _:
                return cls.UNKNOWN

class Anime:
    """
    Classe che rappresenta un anime.

    Attributes:
        name (str): il nome dell'anime.
        ref (str): il riferimento dell'anime.
        anilist_id (int): l'ID dell'anime su Anilist.
        dub (bool): indica se l'anime è doppiato in italiano.
        curr_ep (str): l'episodio corrente.
        last_ep (str): l'ultimo episodio disponibile.
        status (AnimeStatus): lo stato dell'anime.
        info (dict[str, str]): dizionario con le informazioni dell'anime.
    """

    def __init__(self, name: str, ref: str, curr_ep: str = "0", last_ep: str = "0", status: AnimeStatus = AnimeStatus.UNKNOWN) -> None:
        self.name: str = name
        self.ref: str = ref
        self.anilist_id: int = 0
        self.dub: bool = "(ITA)" in name
        self.curr_ep: str = curr_ep
        self.last_ep: str = last_ep if last_ep != "0" else curr_ep
        self.status: AnimeStatus = status
        self._episodes: list[Anime.Episode] = []
        self._num_to_index: dict[str, int] = {}
        self.info: dict[str, str] = {}

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Anime):
            return False

        if self.anilist_id and other.anilist_id:
            return self.anilist_id == other.anilist_id and self.dub == other.dub

        return self.name == other.name # idealmente andrebbe tolto

    def __hash__(self) -> int:
        if self.anilist_id:
            return hash((self.anilist_id, self.dub))

        return hash(self.name)

    def update_episodes(self, episodes: dict[str, str] = {}, specials: bool = True) -> None:
        """
        Imposta i riferimenti degli episodi dell'anime.
        Args:
            episodes (dict[str, str]): dizionario dei riferimenti degli episodi dell'anime (numero->URL/ID).
        """
        for num, ref in episodes.items():
            if not specials and ("." in num or num == "0"):
                continue
            if self.has_episode(num):
                self.episode(num).ref = ref
                continue
            self._episodes.append(Anime.Episode(self, num, ref))

        self._episodes.sort()
        self._num_to_index = {ep.num: i for i, ep in enumerate(self._episodes)}

        if self.has_episode(self.last_ep) and self._episodes[-1] > self.episode(self.last_ep):
            self.last_ep = self._episodes[-1].num

    def episodes(self) -> list[str]:
        """
        Restituisce una lista dei numeri degli episodi disponibili.

        Returns:
            list[str]: la lista dei numeri degli episodi disponibili.
        """
        return list(self._num_to_index.keys())

    def has_episode(self, ep_num: str) -> bool:
        """
        Controlla se l'anime ha l'episodio specificato.
        Args:
            ep_num (str): Il numero dell'episodio.
        Returns:
            (bool): True se l'anime ha l'episodio, False altrimenti.
        """
        return ep_num in self._num_to_index

    def episode(self, ep_num: str) -> Anime.Episode:
        """
        Restituisce il riferimento dell'episodio corrispondente al numero specificato.
        Args:
            ep_num (str): Il numero dell'episodio.
        Returns:
            Anime.Episode : l'episodio corrispondente al numero
        """

        return self._episodes[self._num_to_index[ep_num]]

    def set_info(self, anilist_id: int, status: AnimeStatus, info: dict[str, str]) -> None:
        """
        Imposta le informazioni dell'anime.
        Args:
            anilist_id (int): l'ID di Anilist dell'anime.
            status (AnimeStatus): lo stato dell'anime.
            info (dict): dizionario delle informazioni dell'anime.
        """
        self.anilist_id = anilist_id
        self.info = info
        self.status = status
        self.dub = info.get("Audio", "").lower() == "italiano"

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        """
        Implementazione del protocollo Rich per il rendering della classe.
        """
        yield Text(self.name, style="info")

        tmp_info = dict(self.info)
        tmp_info["Stato"] = self.status.value

        if "Trama" in tmp_info:
             tmp_info["Trama"] = tmp_info.pop("Trama")

        for key, value in tmp_info.items():
            text = Text()
            text.append(f"{key}: ", style="highlight")
            text.append(str(value), style="general")
            yield text

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Anime:
        """
        Crea un oggetto Anime a partire da un dizionario.

        Args:
            data (dict): il dizionario con le informazioni dell'anime.

        Returns:
            Anime: l'oggetto Anime creato.
        """
        anime = Anime(
            name=str(data["name"]),
            ref=str(data["ref"]),
            curr_ep=str(data["curr_ep"]),
            last_ep=str(data["last_ep"])
        )
        id_anilist = data.get("id_anilist")
        status_str = str(data.get("status", "Sconosciuto"))
        info = data.get("info", {})

        anime.set_info(
            anilist_id=int(id_anilist) if isinstance(id_anilist, int) else 0,
            status=AnimeStatus.from_string(status_str),
            info=dict(info) if isinstance(info, dict) else {}
        )

        episodes_data = data["episodes"] if isinstance(data["episodes"], list) else []
        for ep_data in episodes_data:
            anime._episodes = [Anime.Episode.from_dict(anime, ep_data) for ep_data in episodes_data]
            anime.update_episodes()

        return anime

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
            "id_anilist": self.anilist_id,
            "status": self.status.value,
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

        def has_next(self) -> bool:
            """
            Controlla se esiste un episodio successivo.

            Returns:
            bool: True se esiste un episodio successivo, False altrimenti.
            """
            index = self._anime._num_to_index[self.num] + 1
            return index < len(self._anime._episodes)

        def has_prev(self) -> bool:
            """
            Controlla se esiste un episodio precedente.

            Returns:
            bool: True se esiste un episodio precedente, False altrimenti.
            """
            index = self._anime._num_to_index[self.num] - 1
            return index >= 0

        def next(self) -> Anime.Episode:
            """
            Restituisce l'episodio successivo.

            Returns:
            Anime.Episode: l'episodio successivo.
            """
            index = self._anime._num_to_index[self.num] + 1
            return self._anime._episodes[index]

        def prev(self) -> Anime.Episode:
            """
            Restituisce l'episodio precedente.

            Returns:
            Anime.Episode: l'episodio precedente.
            """
            index = self._anime._num_to_index[self.num] - 1
            return self._anime._episodes[index]

        def numeric(self) -> int:
            """
            Restituisce il numero dell'episodio come intero.

            - se è x.5 arrotonda a x.
            - se è x-y restituisce y.

            Returns:
                int: il numero dell'episodio.
            """
            if '.' in self.num:
                return int(self.num.split('.')[0])
            if '-' in self.num:
                return int(self.num.split('-')[1])
            return int(self.num)

        def is_completed(self) -> bool:
            """
            Check if the episode is completed.
            """
            return self.progress == 0 and self.completed

        def set_progress(self, progress: int, completed: bool = False) -> None:
            """
            Imposta il progresso dell'episodio.
            """
            self.progress = progress
            self.completed = completed
            if progress != 0 and not completed:
                self.completed = False

        def mark_completed(self) -> None:
            """
            Segna l'episodio come completato.
            """
            self.progress = 0
            self.completed = True

        @classmethod
        def from_dict(cls, anime: Anime, data: dict[str, object]) -> Anime.Episode:
            """
            Crea un oggetto Episode a partire da un dizionario.

            Args:
                anime (Anime): l'anime a cui appartiene l'episodio.
                data (dict): il dizionario con le informazioni dell'episodio.

            Returns:
                Anime.Episode: l'oggetto Episode creato.
            """
            episode = cls(
                anime,
                num=str(data["num"]),
                ref=str(data["ref"])
            )
            episode.progress = int(data["progress"]) if isinstance(data["progress"], int) else 0
            episode.completed = bool(data["completed"])

            return episode

        def to_dict(self) -> dict[str, object]:
            """
            Restituisce un dizionario con le informazioni dell'episodio.

            Returns:
                dict: il dizionario con le informazioni dell'episodio.
            """
            return {
                "num": self.num,
                "ref": self.ref,
                "progress": self.progress,
                "completed": self.completed
        }
