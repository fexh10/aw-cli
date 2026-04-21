import subprocess
import sys
import re
import socket
import json
import argparse
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from typing import Callable, Optional
from urllib.parse import urlparse, parse_qs

import aw_cli.utilities as ut


class _PreviewHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)
        try:
            index = int(query.get('index', ['0'])[0])
            width = int(query.get('width', ['80'])[0])
        except ValueError:
            index, width = 0, 80

        try:
            res = self.server.preview_callback(index, width)
        except Exception as e:
            res = f"Preview error: {e}"

        try:
            self.send_response(200)
            self.send_header('Content-type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write(res.encode('utf-8'))
        except (BrokenPipeError, ConnectionResetError):
            pass

    def log_message(self, format, *args):
        pass


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

    def run(
        self,
        elements: list[str],
        prompt: str = "> ",
        multi: bool = False,
        filter: bool = False,
        preview_callback: Optional[Callable[[int, int], str]] = None,
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
        preview_server = None
        preview_port = 0

        if preview_callback:
            preview_port = self._find_free_port()
            preview_server = HTTPServer(('127.0.0.1', preview_port), _PreviewHandler)
            preview_server.preview_callback = preview_callback
            Thread(target=preview_server.serve_forever, daemon=True).start()

        cmd = self._build_cmd(
            elements=elements, prompt=prompt, multi=multi, filter=filter, preview_port=preview_port
        )

        try:
            while True:
                process = subprocess.run(
                    cmd,
                    input="\n".join(elements),
                    text=True,
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
            if preview_server:
                preview_server.shutdown()
                preview_server.server_close()

    def reload(self, new_elements: list[str]) -> None:
        """
        Invia un comando reload all'istanza fzf in ascolto tramite --listen.

        Args:
            new_elements: nuove voci con cui aggiornare la lista di fzf.
        """

        escaped = "\n".join(e.replace("'", "'\\''") for e in new_elements)
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

    def refresh_preview(self) -> None:
        """Invia un comando refresh-preview all'istanza fzf in ascolto tramite --listen."""
        req = urllib.request.Request(
            f"http://localhost:{self._port}",
            data=b"refresh-preview",
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
        preview_port: int = 0,
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
            reload_cmd = f"{sys.executable} -c \"from aw_cli.interface.fzf import _main; _main()\" --filter {{q}} --episodes '{json.dumps(elements)}'"
            cmd += [
                "--phony",
                "--bind",
                f"change:reload({reload_cmd})",
                "--header=Range: inizio-fine. crtl+A seleziona tutto, tab/shift+tab selezione singola",
            ]

        if preview_port:
            preview_cmd = f"{sys.executable} -c \"from aw_cli.interface.fzf import _main; _main()\" --preview http://127.0.0.1:{preview_port} --index {{n}} --width $FZF_PREVIEW_COLUMNS"
            cmd += ["--preview", preview_cmd, "--preview-window", "right:50%:wrap"]

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


def _main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--filter", type=str, default="", help="Query per filtrare gli episodi"
    )
    parser.add_argument(
        "--episodes", type=str, required=False, help="Lista episodi JSON"
    )
    parser.add_argument("--preview", type=str, help="URL base per la preview")
    parser.add_argument("--index", type=int, help="Indice elemento in fzf")
    parser.add_argument("--width", type=int, default=80, help="Larghezza finestra preview")
    args = parser.parse_args()

    if args.preview:
        req = urllib.request.Request(f"{args.preview}?index={args.index}&width={args.width}")
        try:
            with urllib.request.urlopen(req, timeout=3) as res:
                print(res.read().decode('utf-8'))
        except OSError:
            pass
    elif args.episodes:
        _filter_episodes(args.filter, args.episodes)


if __name__ == "__main__":
    _main()
