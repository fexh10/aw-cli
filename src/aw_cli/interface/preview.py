import threading
import time
from io import StringIO
from typing import Callable, Optional

from rich.console import Console
from rich.theme import Theme

from ..anime import Anime
from ..providers.provider import Provider
from .. import utilities as ut
from .fzf import Fzf


class AnimePreview:
    def __init__(self, provider: Provider, animelist: list[Anime], fzf: Optional[Fzf] = None):
        self.provider = provider
        self.animelist = animelist
        self.fzf = fzf
        self._fetching = {}
        self._lock = threading.Lock()
        self._current_index = -1

    def __call__(self, index: int, width: int) -> str:
        self._current_index = index
        
        try:
            # `list_anime_names` iterates reversed over animelist. So fzf index 0 is animelist[-1]
            anime_idx = len(self.animelist) - 1 - index
            anime = self.animelist[anime_idx]
        except IndexError:
            return ""

        if "Trama" in anime.info:
            return self._render(anime, width)

        with self._lock:
            if index not in self._fetching:
                self._fetching[index] = True
                threading.Thread(target=self._background_fetch, args=(index, width, anime), daemon=True).start()

        partial = self._render(anime, width)
        return partial + "\n[Caricamento trama...]"

    def _background_fetch(self, index: int, width: int, anime: Anime) -> None:
        time.sleep(0.35)
        if self._current_index != index:
            with self._lock:
                self._fetching.pop(index, None)
            return

        try:
            self.provider.info_anime(anime)
        except LookupError:
            pass
        finally:
            with self._lock:
                self._fetching.pop(index, None)
            
            if self.fzf:
                self.fzf.refresh_preview()

    def _render(self, anime: Anime, width: int) -> str:
        sio = StringIO()
        
        style = ut.config_data.get("style", ut.DEFAULT_STYLE)
        theme = Theme(style)
        
        console = Console(file=sio, force_terminal=True, color_system="truecolor", width=width, theme=theme)
        console.print(anime)
        return sio.getvalue()
