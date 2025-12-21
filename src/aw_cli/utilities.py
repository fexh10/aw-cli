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

def fzf(elements: list[str], prompt: str = "> ", multi: bool = False) -> str:
    """
    Avvia fzf con impostazioni predefinite.

    Args:
        elements (list[str]): lista da passare ad fzf con gli elementi da selezionare.
        prompt (str, optional): il prompt che fzf deve stampare. Valore predefinito: "> ".
        multi (bool, optional): se True, permette la selezione multipla, con aggiunta di un costum bind crtl+a che
         permette di selezionare tutto. Valore predefinito: False.

    Returns:
        str: la scelta selezionata tramite fzf.
    """
    cmd = ["fzf", "--tac", f"--height={len(elements) + 2}", "--cycle", "--ansi", "--tiebreak=begin", f"--prompt={prompt}"]
    if multi:
        cmd += ["--multi", "--bind", "ctrl-a:toggle-all"]

    while True:
        process = subprocess.run(
            cmd,
            input="\n".join(elements),
            text=True,
            stdout=subprocess.PIPE,
            stderr=None
        )

        if process.returncode == 130:
            exit()

        if process.stdout.strip():
            return process.stdout.strip()
