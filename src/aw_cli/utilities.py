import os
import toml
import subprocess
from time import sleep
from rich.console import Console
from rich.theme import Theme

from rich.prompt import Prompt, FloatPrompt
from collections import defaultdict

configData = defaultdict(dict)

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
    nome_os = out[0]
    if nome_os == "Linux":
        if "Android" == out[-1]:
            nome_os = "Android"
        elif "WSL" in out[2]:
            nome_os = "WSL"
    return nome_os

nome_os = get_os()

def sanitize_filename(filename: str) -> str:
    """
    Sanitizza il nome del file rimuovendo i caratteri non validi.

    Args:
        filename (str): il nome del file da sanitizzare.

    Returns:
        str: il nome del file sanitizzato.
    """
    if nome_os != "Android":
        return filename

    forbidden_char = '"*/:<>?\\|'
    replace_char = '”⁎∕꞉‹›︖＼⏐'
    for a, b in zip(forbidden_char, replace_char):
        filename = filename.replace(a, b)
    return filename

def getConfig() -> None:
    """
    Prende le impostazioni scelte dall'utente
    dal file di configurazione.

    Returns:
        None
    """
    global configData

    configPath = f"{os.path.dirname(__file__)}/config.toml"

    with open(configPath, 'r') as f:
        configData = toml.load(f)

    # Merge with default styles if missing
    if "style" not in configData:
        configData["style"] = DEFAULT_STYLE.copy()
    else:
        for key, value in DEFAULT_STYLE.items():
            if key not in configData["style"]:
                configData["style"][key] = value

    global console
    console = Console(theme=Theme(configData["style"]), highlight=False)

    if nome_os == "WSL":
        configData["player"]["path"] = f'''"$(wslpath '{configData["player"]["path"]}')"'''
        if "syncplay" in configData:
            configData["syncplay"]["path"] = f"/mnt/c/Windows/System32/cmd.exe /C '{configData['syncplay']['path']}'"

    if "specials" not in configData["general"]:
        configData["general"]["specials"] = False
