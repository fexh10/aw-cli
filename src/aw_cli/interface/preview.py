import shutil
import subprocess
import threading
import time
import urllib.request
import sys
import os
import termios
import tty
import select
from io import StringIO
from typing import Callable, Optional

from rich.console import Console
from rich.theme import Theme

from ..anime import Anime
from ..providers.provider import Provider
from .. import utilities as ut
from .fzf import Fzf


class AnimePreview:
    def __init__(
        self, provider: Provider, animelist: list[Anime], fzf: Optional[Fzf] = None
    ):
        self.provider = provider
        self.animelist = animelist
        self.fzf = fzf
        self._fetching = {}
        self._lock = threading.Lock()
        self._current_index = -1
        self._rendered_images: dict[str, str] = {}

        # Rilevamento automatico del formato supportato
        self._chafa_format = self._detect_best_chafa_format()

    def _detect_best_chafa_format(self) -> str:
        """Determina se il terminale supporta sixel, altrimenti ripiega su symbols."""
        if not shutil.which("chafa"):
            return ""

        # Se siamo su Termux (app standard), spesso il supporto Sixel è assente
        # Interroghiamo il terminale con la sequenza Device Attributes (\033[c)
        if self._check_sixel_support():
            return "sixels"

        # Fallback sicuro che non produce geroglifici
        return "symbols"

    def _check_sixel_support(self) -> bool:
        """Interroga il terminale per il supporto Sixel (parametro 4)."""
        # Se non è un terminale interattivo o siamo in una pipe, non possiamo interrogare
        if not sys.stdout.isatty():
            return False

        try:
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                # Invia sequenza Device Attributes
                sys.stdout.write("\033[c")
                sys.stdout.flush()

                # Timeout di 0.2s per la risposta del terminale
                if select.select([sys.stdin], [], [], 0.2)[0]:
                    response = ""
                    while True:
                        char = sys.stdin.read(1)
                        response += char
                        if char == "c":
                            break

                    # Cerca il numero '4' nei parametri della risposta
                    params = response.lstrip("\033[?").rstrip("c").split(";")
                    return "4" in params
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        except Exception:
            pass
        return False

    def _fetch_and_render_image(self, cover_url: str, width: int) -> str:
        if not self._chafa_format:
            return ""

        try:
            req = urllib.request.Request(
                cover_url, headers={"User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                image_bytes = response.read()

            w = max(width - 2, 10)
            # Usa il formato rilevato (sixels o symbols)
            result = subprocess.run(
                ["chafa", "-f", self._chafa_format, "-s", f"{w}x18", "-"],
                input=image_bytes,
                capture_output=True,
            )
            if result.returncode == 0:
                # Aggiungiamo un newline per separare l'immagine dal testo
                return result.stdout.decode("utf-8", errors="ignore") + "\n\n"
        except Exception:
            pass

        return ""

    def __call__(self, index: int, width: int) -> str:
        self._current_index = index

        try:
            anime_idx = len(self.animelist) - 1 - index
            anime = self.animelist[anime_idx]
        except IndexError:
            return ""

        cover_url = anime.info.get("Cover") if anime.info else None
        img_ansi = ""

        if cover_url:
            if cover_url not in self._rendered_images:
                self._rendered_images[cover_url] = self._fetch_and_render_image(
                    cover_url, width
                )
            img_ansi = self._rendered_images[cover_url]

        if "Trama" in anime.info:
            return img_ansi + self._render(anime, width)

        with self._lock:
            if index not in self._fetching:
                self._fetching[index] = True
                threading.Thread(
                    target=self._background_fetch,
                    args=(index, width, anime),
                    daemon=True,
                ).start()

        partial = self._render(anime, width)
        return img_ansi + partial + "\n[Caricamento trama...]"

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

        console = Console(
            file=sio,
            force_terminal=True,
            color_system="truecolor",
            width=width,
            theme=theme,
        )
        console.print(anime)
        return sio.getvalue()
