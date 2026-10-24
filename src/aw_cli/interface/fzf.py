import os
import subprocess
import sys
import re
import socket
import json
import argparse
import tempfile
import urllib.request
from .. import utilities as ut


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
        self._temp_files: list[str] = []
        self._win_reload: bool = sys.platform == "win32"

    def _cleanup_temp_files(self) -> None:
        temp_files = getattr(self, "_temp_files", None)
        if not temp_files:
            return
        for path in temp_files:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except OSError:
                pass
        temp_files.clear()

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
        self._port = self._find_free_port()
        cmd = self._build_cmd(
            elements=elements, prompt=prompt, multi=multi, filter=filter
        )
        fzf_bin = ut.find_binary("fzf")
        if fzf_bin and cmd and cmd[0] == "fzf":
            cmd[0] = fzf_bin

        try:
            while True:
                process = subprocess.run(
                    cmd,
                    input="\n".join(elements),
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    stdout=subprocess.PIPE,
                    stderr=None,
                )

                if process.returncode == 130:
                    exit()

                if process.stdout.strip():
                    return process.stdout.strip()
        except KeyboardInterrupt:
            exit()
        finally:
            self._cleanup_temp_files()

    def reload(self, new_elements: list[str]) -> None:
        """
        Invia un comando reload all'istanza fzf in ascolto tramite --listen.

        Args:
            new_elements: nuove voci con cui aggiornare la lista di fzf.
        """
        if getattr(self, "_win_reload", False):
            with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as f:
                f.write("\n".join(new_elements))
                temp_name = f.name
            if not hasattr(self, "_temp_files"):
                self._temp_files = []
            self._temp_files.append(temp_name)
            action = f'reload(type "{temp_name}")'
        else:
            escaped = "\n".join(e.replace("'", "'\\''") for e in new_elements)
            action = f"reload(printf '{escaped}')"

        req = urllib.request.Request(
            f"http://localhost:{self._port}",
            data=action.encode("utf-8"),
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
        Restituisce una porta TCP libera assegnata dal sistema operativo su 127.0.0.1.
        Usare questa porta per --listen evita conflitti e TIME_WAIT tra riavvii di fzf.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
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
            if sys.platform == "win32":
                with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as f:
                    json.dump(elements, f)
                    ep_file = f.name
                if not hasattr(self, "_temp_files"):
                    self._temp_files = []
                self._temp_files.append(ep_file)
                reload_cmd = f'"{sys.executable}" -m aw_cli.interface.fzf --filter {{q}} --episodes-file "{ep_file}" --episodes \'{json.dumps(elements)}\''
            else:
                reload_cmd = f"{sys.executable} -m aw_cli.interface.fzf --filter {{q}} --episodes '{json.dumps(elements)}'"
            cmd += [
                "--phony",
                "--bind",
                f"change:reload({reload_cmd})",
                "--header=Range: inizio-fine. crtl+A seleziona tutto, tab/shift+tab selezione singola",
            ]

        return cmd


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

    if "-" in query:
        parts = query.split("-", 1)
        try:
            lo = float(parts[0]) if parts[0] else None
            hi = float(parts[1]) if parts[1] else None

            for e in episodes:
                e_lo, e_hi = None, None
                if "-" in e:
                    e_parts = e.split("-", 1)
                    try:
                        e_lo = float(e_parts[0]) if e_parts[0] else None
                        e_hi = float(e_parts[1]) if e_parts[1] else None
                    except ValueError:
                        continue
                else:
                    try:
                        e_lo = e_hi = float(e)
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
            try:
                if re.search(query, e):
                    print(e)
            except re.error:
                if query in e:
                    print(e)


if __name__ == "__main__":
    if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--filter", type=str, default="", help="Query per filtrare gli episodi"
    )
    parser.add_argument(
        "--episodes", type=str, default="", help="Lista episodi JSON"
    )
    parser.add_argument(
        "--episodes-file", type=str, default="", help="File JSON con lista episodi"
    )
    args, _ = parser.parse_known_args()

    episodes_raw = args.episodes
    if args.episodes_file:
        try:
            with open(args.episodes_file, "r", encoding="utf-8") as f:
                episodes_raw = f.read()
        except OSError:
            pass

    _filter_episodes(args.filter, episodes_raw)
