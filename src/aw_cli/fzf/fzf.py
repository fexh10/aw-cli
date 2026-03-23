import subprocess
import urllib.request

import aw_cli.utilities as ut
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
        self._port: int = ut.config_data.get("fzf", {}).get("port", 4321)

    def run(
        self,
        elements: list[str],
        prompt: str = "> ",
        multi: bool = False,
    ) -> str:
        """
        Avvia fzf e restituisce la selezione dell'utente.

        Args:
            elements: voci da visualizzare in fzf.
            prompt:   testo del prompt.
            multi:    se True abilita la selezione multipla (Ctrl+A = toggle all).

        Returns:
            Stringa selezionata (più righe separate da '\\n' in modalità multi).
        """

        cmd = self._build_cmd(elements=elements, prompt=prompt, multi=multi)

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

    def reload(self, new_elements: list[str]) -> None:
        """
        Invia un comando reload all'istanza fzf in ascolto tramite --listen.

        Args:
            new_elements: nuove voci con cui aggiornare la lista di fzf.
        """
        # Escape single-quote POSIX: ' → '\'' così la shell non rompe il printf
        escaped = "\n".join(e.replace("'", "'\\''"  ) for e in new_elements)
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

    def _build_cmd(self, elements: list[str], prompt: str, multi: bool) -> list[str]:
        """
        Costruisce la lista di argomenti per il processo fzf.
        """

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

        return cmd
