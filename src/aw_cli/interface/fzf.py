import subprocess
import sys
import re
import socket
import json
import argparse
import urllib.request
from rich.text import Text
from .console import console
from ..core.config import config


class Fzf:
    """
    Wrapper attorno a fzf con supporto per il reload dinamico tramite --listen.
    """

    _DEFAULTS: dict[str, str | bool] = {
        "tac": True,
        "cycle": True,
        "ansi": True,
        "tiebreak": "begin",
    }

    def __init__(self):
        self._port: int = 0
        self.elements: list[str] = []
        self.rendered_elements: list[str] = []

    def _render_elements(self, elements: list[str]) -> list[str]:
        rendered = []
        for e in elements:
            with console.capture() as capture:
                console.print(e, end="")
            rendered.append(capture.get())
        return rendered

    def _ansi_to_plain(self, selected_ansi: str) -> str:
        selected_lines = selected_ansi.split("\n")
        result_lines = []
        for line in selected_lines:
            try:
                idx = self.rendered_elements.index(line)
                original_el = self.elements[idx]
                result_lines.append(Text.from_markup(original_el).plain)
            except ValueError:
                result_lines.append(Text.from_ansi(line).plain)
        return "\n".join(result_lines)

    def run(
        self,
        elements: list[str],
        prompt: str = "> ",
        multi: bool = False,
        filter: bool = False,
    ) -> str:
        """
        Avvia fzf e restituisce la selezione dell'utente.

        Args:
            elements: voci da visualizzare in fzf.
            prompt:   testo del prompt.
            multi:    se True abilita la selezione multipla (Ctrl+A = toggle all).
            filter:   se True abilita il filtro per range (formato: inizio-fine).
        """
        # Converte il prompt usando lo stile "prompt" configurato
        with console.capture() as capture:
            console.print(f"[prompt]{prompt}[/]", end="")
        ansi_prompt = capture.get()

        self.elements = elements
        self.rendered_elements = self._render_elements(elements)

        self._port = self._find_free_port()
        cmd = self._build_cmd(
            elements=self.rendered_elements, prompt=ansi_prompt, multi=multi, filter=filter
        )

        try:
            while True:
                process = subprocess.run(
                    cmd,
                    input="\n".join(self.rendered_elements),
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=None,
                )

                if process.returncode == 130:
                    exit()

                selected_ansi = process.stdout.strip()
                if selected_ansi:
                    return self._ansi_to_plain(selected_ansi)
        except KeyboardInterrupt:
            exit()

    def reload(self, new_elements: list[str]) -> None:
        """
        Invia un comando reload all'istanza fzf in ascolto tramite --listen.

        Args:
            new_elements: nuove voci con cui aggiornare la lista di fzf.
        """
        self.elements = new_elements
        self.rendered_elements = self._render_elements(new_elements)

        escaped = "\n".join(e.replace("'", "'\\''") for e in self.rendered_elements)
        action = f"reload(printf '{escaped}')"

        req = urllib.request.Request(
            f"http://localhost:{self._port}",
            data=action.encode(),
            method="POST",
        )
        req.add_header("Content-Type", "text/plain")

        try:
            with urllib.request.urlopen(req, timeout=3):
                pass
        except OSError:
            pass

    @staticmethod
    def _find_free_port() -> int:
        """
        Restituisce una porta TCP libera assegnata dal sistema operativo.
        Usare questa porta per --listen evita conflitti e TIME_WAIT tra riavvii di fzf.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", 0))
            return s.getsockname()[1]

    def _build_cmd(
        self,
        elements: list[str],
        prompt: str,
        multi: bool,
        filter: bool = False,
    ) -> list[str]:
        """Costruisce la lista di argomenti per il processo fzf."""
        cmd = ["fzf", "--listen", str(self._port)]

        if "height" not in self._DEFAULTS:
            cmd += [f"--height={len(elements) + 2}"]

        for key, value in self._DEFAULTS.items():
            flag = f"--{key}"
            if isinstance(value, bool):
                if value:
                    cmd.append(flag)
            else:
                cmd += [flag, str(value)]

        cmd += [f"--prompt={prompt}"]

        if multi:
            cmd += ["--multi", "--bind", "ctrl-a:toggle-all"]

        if filter:
            reload_cmd = f"{sys.executable} -m aw_cli.interface.fzf --filter {{q}} --episodes '{json.dumps(elements)}'"
            cmd += [
                "--phony",
                "--bind",
                f"change:reload({reload_cmd})",
                "--header=Range: inizio-fine. crtl+A seleziona tutto, tab/shift+tab selezione singola",
            ]

        cmd += self._get_color_args()

        return cmd

    def _get_color_args(self) -> list[str]:
        from rich.style import Style
        styles = config.data.get("style", {})
        mapping = {
            "general": ["fg", "fg+"],
            "prompt": ["prompt"],
        }

        color_options = []
        for key, fzf_keys in mapping.items():
            if style_str := styles.get(key):
                try:
                    style = Style.parse(style_str)
                    if style.color:
                        color = str(style.color.number) if style.color.number is not None else style.color.name.replace("_", "-")
                        if style.bold:
                            color += ":bold"
                        for fzf_key in fzf_keys:
                            color_options.append(f"{fzf_key}:{color}")
                except Exception:
                    pass

        return ["--color", ",".join(color_options)] if color_options else []


def _strip_ansi(text: str) -> str:
    """Rimuove le sequenze di escape ANSI da una stringa."""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)


def _filter_episodes(query: str, episodes_raw: str) -> None:
    """
    Filtra gli episodi in base alla query e stampa il risultato su stdout.

    Formati query:
      - "5-10" → episodi con numero nell'intervallo [5, 10]
      - "5-"   → episodi con numero >= 5
      - "7"    → episodi che contengono "7" (sottostringa)

    Un episodio stesso può essere un range (es. "29-30"). Il filtro
    ha successo se i due intervalli si intersecano.
    """

    try:
        episodes: list[str] = json.loads(episodes_raw)
    except (json.JSONDecodeError, ValueError):
        return

    if not query:
        print("\n".join(episodes))
        return

    query_clean = _strip_ansi(query)

    if "-" in query_clean:
        parts = query_clean.split("-", 1)
        try:
            lo = float(parts[0]) if parts[0] else None
            hi = float(parts[1]) if parts[1] else None

            for e in episodes:
                e_clean = _strip_ansi(e)
                e_lo, e_hi = None, None
                if "-" in e_clean:
                    e_parts = e_clean.split("-", 1)
                    try:
                        e_lo = float(e_parts[0]) if e_parts[0] else None
                        e_hi = float(e_parts[1]) if e_parts[1] else None
                    except ValueError:
                        continue
                else:
                    try:
                        e_lo = e_hi = float(e_clean)
                    except ValueError:
                        continue

                if e_lo is None or e_hi is None:
                    continue

                if lo is not None and hi is not None:
                    if max(lo, e_lo) <= min(hi, e_hi):
                        print(e)
                elif lo is not None:
                    if e_hi >= lo:
                        print(e)
                elif hi is not None:
                    if e_lo <= hi:
                        print(e)
        except ValueError:
            pass
    else:
        for e in episodes:
            e_clean = _strip_ansi(e)
            try:
                if re.search(query_clean, e_clean):
                    print(e)
            except re.error:
                if query_clean in e_clean:
                    print(e)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--filter", type=str, default="", help="Query per filtrare gli episodi"
    )
    parser.add_argument(
        "--episodes", type=str, required=True, help="Lista episodi JSON"
    )
    args = parser.parse_args()

    _filter_episodes(args.filter, args.episodes)
