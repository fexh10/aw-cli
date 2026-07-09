import subprocess
import sys
from pathlib import Path


class Environment:
    """
    Rileva e incapsula le informazioni sul sistema operativo corrente.
    Fornisce proprietà semantiche e utilità di sistema.
    """

    def __init__(self):
        self.os_name = self._detect_os()

    @staticmethod
    def _detect_os() -> str:
        """
        Rileva il sistema operativo corrente, gestendo casi specifici
        come Android (Termux) e WSL (Windows Subsystem for Linux).
        """
        if sys.platform == "win32":
            return "Windows"
        if sys.platform == "darwin":
            return "Darwin"

        try:
            result = subprocess.run(
                ["uname", "-a"], capture_output=True, text=True, check=False
            )
            out = result.stdout.strip().split()
            if not out:
                return "Linux"

            os_name = out[0]
            if os_name == "Linux":
                if "Android" == out[-1]:
                    return "Android"
                elif len(out) > 2 and "WSL" in out[2]:
                    return "WSL"
            return os_name
        except FileNotFoundError:
            return "Linux"

    # -- Proprietà semantiche --

    @property
    def is_android(self) -> bool:
        return self.os_name == "Android"

    @property
    def is_wsl(self) -> bool:
        return self.os_name == "WSL"

    @property
    def is_macos(self) -> bool:
        return self.os_name == "Darwin"

    @property
    def supports_syncplay(self) -> bool:
        """Syncplay non è supportato su Android."""
        return not self.is_android

    @property
    def default_download_path(self) -> Path:
        """Ritorna il percorso di download predefinito per la piattaforma corrente."""
        if self.is_android:
            return Path("/sdcard/Movies/Anime")
        return Path.home() / "Videos/Anime"

    # -- Utilità di sistema --

    def open_url(self, url: str) -> None:
        """Apre un URL nel browser predefinito del sistema."""
        cmd = "open" if self.is_macos else "xdg-open"
        subprocess.run(
            f"{cmd} '{url}'",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def wrap_path_for_wsl(self, path: str, syncplay: bool = False) -> str:
        """Applica il wrapper wslpath al percorso del player se siamo in WSL."""
        if not self.is_wsl:
            return path

        if syncplay:
            return f"/mnt/c/Windows/System32/cmd.exe /C '{path}'"
        return f'''"$(wslpath '{path}')"'''

    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitizza il nome del file per i vincoli del filesystem della piattaforma corrente
        (es. restrizioni sui caratteri speciali di Android).
        """
        if not self.is_android:
            return filename

        forbidden_char = '"*/:<>?\\|'
        replace_char = '”⁎∕꞉‹›︖＼⏐'
        for a, b in zip(forbidden_char, replace_char):
            filename = filename.replace(a, b)
        return filename


# Istanza singleton
env = Environment()
