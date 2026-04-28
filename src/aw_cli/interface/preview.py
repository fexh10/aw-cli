import shutil
import subprocess
import sys
import os
import termios
import tty
import select
from io import StringIO
from typing import Optional
from pathlib import Path

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
        self._rendered_images: dict[str, str] = {}

        # Rilevamento automatico del formato supportato
        self._chafa_format = self._detect_best_chafa_format()

    def _detect_best_chafa_format(self) -> str:
        """Determina se il terminale supporta sixel, altrimenti ripiega su symbols."""
        if not shutil.which("chafa"):
            return ""

        if self._check_sixel_support():
            return "sixels"

        return "symbols"

    def _check_sixel_support(self) -> bool:
        """Interroga il terminale per il supporto Sixel (parametro 4)."""
        if not sys.stdout.isatty():
            return False

        try:
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                sys.stdout.write("\033[c")
                sys.stdout.flush()

                if select.select([sys.stdin], [], [], 0.2)[0]:
                    response = ""
                    while True:
                        char = sys.stdin.read(1)
                        response += char
                        if char == "c":
                            break

                    params = response.lstrip("\033[?").rstrip("c").split(";")
                    return "4" in params
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        except Exception:
            pass
        return False

    def _render_image(self, img_path: Path, width: int) -> str:
        """Renderizza un file immagine con chafa. Cache in RAM per evitare chiamate ripetute."""
        cache_key = str(img_path)
        if cache_key in self._rendered_images:
            return self._rendered_images[cache_key]

        if not self._chafa_format:
            return ""

        try:
            w = max(width - 2, 10)
            result = subprocess.run(
                ["chafa", "-f", self._chafa_format, "-s", f"{w}x18", str(img_path)],
                capture_output=True,
            )
            if result.returncode == 0:
                rendered = result.stdout.decode("utf-8", errors="ignore") + "\n\n"
                self._rendered_images[cache_key] = rendered
                return rendered
        except Exception:
            pass

        return ""

    def __call__(self, index: int, width: int) -> str:
        try:
            anime_idx = len(self.animelist) - 1 - index
            anime = self.animelist[anime_idx]
        except IndexError:
            return ""

        # Fetch info in modo sincrono (istantaneo se in cache disco)
        try:
            self.provider.info_anime(anime)
        except Exception:
            pass

        # Fetch immagine dal provider (istantaneo se in cache disco)
        img_ansi = ""
        img_path = self.provider.cover_image(anime)
        if img_path:
            img_ansi = self._render_image(img_path, width)

        return img_ansi + self._render_text(anime, width)

    def _render_text(self, anime: Anime, width: int) -> str:
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
