import os
import sys
import shutil
import string
import platform
import subprocess
import toml
from pathlib import Path
from rich.console import Console
from rich.theme import Theme
from collections import defaultdict

if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stdin, "reconfigure"):
            sys.stdin.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

config_data = defaultdict(dict)

DEFAULT_STYLE = {
    "error": "bold red",
    "prompt": "bold light_sky_blue3",
    "warning": "bold yellow",
    "success": "bold green",
    "info": "bright_yellow",
    "highlight": "cyan",
    "general": "white",
}

console = Console(
    theme=Theme(DEFAULT_STYLE),
    highlight=False,
    legacy_windows=False if sys.platform == "win32" else None,
)


def get_os() -> str:
    """Rileva il sistema operativo corrente in modo compatibile multipiattaforma."""
    if platform.system() == "Windows":
        return "Windows"
    try:
        result = subprocess.run(
            ["uname", "-a"], capture_output=True, text=True, check=False
        )
        out = result.stdout.strip().split()
        if not out:
            return platform.system()
        os_name_val = out[0]
        if os_name_val == "Linux":
            if "Android" == out[-1]:
                os_name_val = "Android"
            elif len(out) > 2 and "WSL" in out[2]:
                os_name_val = "WSL"
        return os_name_val
    except Exception:
        return platform.system()


os_name = get_os()


def get_data_dir() -> Path:
    """
    Restituisce la directory dei dati utente (config.toml, history.json).
    Supporta installazioni portabili o su dischi secondari tramite AW_CLI_HOME
    o file marker 'portable.txt', ed esegue la migrazione automatica di eventuali
    file legacy presenti nella cartella del pacchetto.
    """
    env_home = os.environ.get("AW_CLI_HOME")
    if env_home:
        data_dir = Path(env_home).expanduser()
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir

    pkg_dir = Path(__file__).parent
    if (pkg_dir / "portable.txt").exists():
        return pkg_dir

    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        base = Path(appdata) if appdata else (Path.home() / "AppData" / "Roaming")
        data_dir = base / "aw-cli"
    elif os_name == "Android":
        data_dir = pkg_dir
    else:
        xdg_config = os.environ.get("XDG_CONFIG_HOME")
        base = Path(xdg_config) if xdg_config else (Path.home() / ".config")
        data_dir = base / "aw-cli"

    try:
        data_dir.mkdir(parents=True, exist_ok=True)
        # Migrazione automatica da eventuale installazione precedente in pkg_dir
        for fname in ("config.toml", "history.json", "aw-cronologia.csv"):
            legacy_file = pkg_dir / fname
            target_file = data_dir / fname
            if legacy_file.exists() and not target_file.exists():
                try:
                    shutil.copy2(legacy_file, target_file)
                except OSError:
                    pass
        return data_dir
    except OSError:
        return pkg_dir


def get_config_path() -> Path:
    """Restituisce il percorso del file config.toml."""
    return get_data_dir() / "config.toml"


def get_available_drives() -> list[tuple[str, float]]:
    """
    Restituisce la lista dei dischi montati su Windows con lo spazio libero in GB.
    Formato: [('C:\\', 55.6), ('D:\\', 425.7), ...]
    """
    drives: list[tuple[str, float]] = []
    if sys.platform != "win32":
        return drives
    for letter in string.ascii_uppercase:
        root = f"{letter}:\\"
        if os.path.exists(root):
            try:
                usage = shutil.disk_usage(root)
                free_gb = round(usage.free / (1024**3), 1)
                drives.append((root, free_gb))
            except OSError:
                pass
    return drives


def find_binary(name: str) -> str | None:
    """
    Cerca un eseguibile (mpv, vlc, fzf, ffmpeg, syncplay) nel PATH,
    nelle cartelle WinGet/Scoop e su tutti i dischi installati (primario e secondari).
    """
    if sys.platform == "win32" and name.lower() == "mpv":
        direct = shutil.which("mpv.com") or shutil.which("mpv")
        if direct:
            p = Path(direct)
            if p.suffix.lower() == ".exe" and p.with_suffix(".com").exists():
                return str(p.with_suffix(".com"))
            return direct
    else:
        direct = shutil.which(name)
        if direct:
            return direct

    if sys.platform != "win32":
        return None

    exe_names = (
        ["mpv.com", "mpv.exe"]
        if name.lower() == "mpv"
        else [f"{name}.exe", f"{name}.cmd", f"{name}.bat"]
    )

    # 1. Controlla pacchetti WinGet nell'ambiente utente
    local_appdata = os.environ.get("LOCALAPPDATA")
    if local_appdata:
        winget_pkgs = Path(local_appdata) / "Microsoft" / "WinGet" / "Packages"
        if winget_pkgs.exists():
            for exe in exe_names:
                for match in winget_pkgs.rglob(exe):
                    if match.is_file():
                        return str(match)

    # 2. Controlla su tutti i dischi montati (es. C:\, D:\, E:\, G:\)
    relative_dirs = [
        "Program Files\\mpv",
        "Program Files (x86)\\mpv",
        "mpv",
        "Program Files\\VideoLAN\\VLC",
        "Program Files (x86)\\VideoLAN\\VLC",
        "VLC",
        "Program Files\\Syncplay",
        "Program Files (x86)\\Syncplay",
        "Syncplay",
        "ffmpeg\\bin",
        "Program Files\\ffmpeg\\bin",
        "Tools",
        "Scoop\\shims",
    ]

    for root, _ in get_available_drives():
        drive_path = Path(root)
        for rel in relative_dirs:
            folder = drive_path / rel
            if folder.exists():
                for exe in exe_names:
                    candidate = folder / exe
                    if candidate.is_file():
                        return str(candidate)

    return None


def sanitize_filename(filename: str) -> str:
    """
    Sanitizza il nome del file rimuovendo i caratteri non validi e prevenendo path traversal.

    Args:
        filename (str): il nome del file da sanitizzare.

    Returns:
        str: il nome del file sanitizzato.
    """
    filename = "".join(c for c in filename if ord(c) >= 32 and ord(c) != 127)
    while ".." in filename:
        filename = filename.replace("..", "．．")

    if os_name not in ("Android", "Windows"):
        return filename.replace("/", "∕").strip()

    forbidden_char = '"*/:<>?\\|'
    replace_char = "”⁎∕꞉‹›︖＼⏐"
    for a, b in zip(forbidden_char, replace_char):
        filename = filename.replace(a, b)
    filename = filename.strip().rstrip(".")
    return filename or "Anime"


def get_config() -> None:
    """
    Prende le impostazioni scelte dall'utente
    dal file di configurazione.

    Returns:
        None
    """
    global config_data

    config_path = get_config_path()
    if not config_path.exists():
        fallback = Path(__file__).parent / "config.toml"
        if fallback.exists():
            config_path = fallback

    with open(config_path, "r", encoding="utf-8") as f:
        config_data = toml.load(f)

    if "style" not in config_data:
        config_data["style"] = DEFAULT_STYLE.copy()
    else:
        for key, value in DEFAULT_STYLE.items():
            if key not in config_data["style"]:
                config_data["style"][key] = value

    global console
    console = Console(
        theme=Theme(config_data["style"]),
        highlight=False,
        legacy_windows=False if sys.platform == "win32" else None,
    )

    if os_name == "WSL":
        config_data["player"]["path"] = (
            f'''"$(wslpath '{config_data["player"]["path"]}')"'''
        )
        if "syncplay" in config_data:
            config_data["syncplay"]["path"] = (
                f"/mnt/c/Windows/System32/cmd.exe /C '{config_data['syncplay']['path']}'"
            )

    if "general" not in config_data:
        config_data["general"] = {}
    if "specials" not in config_data["general"]:
        config_data["general"]["specials"] = False
