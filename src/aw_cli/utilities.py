import toml
import subprocess
from pathlib import Path
from rich.console import Console
from rich.theme import Theme
from collections import defaultdict

config_data = defaultdict(dict)

DEFAULT_STYLE = {
    "error": "bold red",
    "prompt": "bold light_sky_blue3",
    "warning": "bold yellow",
    "success": "bold green",
    "info": "bright_yellow",
    "highlight": "cyan",
    "general": "white"
}

console = Console(theme=Theme(DEFAULT_STYLE), highlight=False)

# controllo il tipo del dispositivo
def get_os() -> str:
    result = subprocess.run(["uname", "-a"], capture_output=True, text=True, check=False)
    out = result.stdout.strip().split()
    os_name = out[0]
    if os_name == "Linux":
        if "Android" == out[-1]:
            os_name = "Android"
        elif "WSL" in out[2]:
            os_name = "WSL"
    return os_name

os_name = get_os()

def sanitize_filename(filename: str) -> str:
    """
    Sanitizza il nome del file rimuovendo i caratteri non validi.

    Args:
        filename (str): il nome del file da sanitizzare.

    Returns:
        str: il nome del file sanitizzato.
    """
    if os_name != "Android":
        return filename

    forbidden_char = '"*/:<>?\\|'
    replace_char = '”⁎∕꞉‹›︖＼⏐'
    for a, b in zip(forbidden_char, replace_char):
        filename = filename.replace(a, b)
    return filename

def get_config() -> None:
    """
    Prende le impostazioni scelte dall'utente
    dal file di configurazione.

    Returns:
        None
    """
    global config_data

    config_path = Path(__file__).parent / "config.toml"

    with open(config_path, 'r') as f:
        config_data = toml.load(f)

    # Merge with default styles if missing
    if "style" not in config_data:
        config_data["style"] = DEFAULT_STYLE.copy()
    else:
        for key, value in DEFAULT_STYLE.items():
            if key not in config_data["style"]:
                config_data["style"][key] = value

    global console
    console = Console(theme=Theme(config_data["style"]), highlight=False)

    if os_name == "WSL":
        config_data["player"]["path"] = f'''"$(wslpath '{config_data["player"]["path"]}')"'''
        if "syncplay" in config_data:
            config_data["syncplay"]["path"] = f"/mnt/c/Windows/System32/cmd.exe /C '{config_data['syncplay']['path']}'"

    if "specials" not in config_data["general"]:
        config_data["general"]["specials"] = False

    if "cache" not in config_data:
        config_data["cache"] = {}
    config_data["cache"].setdefault("ttl_ongoing_hours", 1)       # 1 ora
    config_data["cache"].setdefault("ttl_unreleased_hours", 24)   # 24 ore
    config_data["cache"].setdefault("ttl_finished_days", 30)      # 30 giorni
