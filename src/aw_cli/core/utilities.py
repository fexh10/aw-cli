import toml
from pathlib import Path
from rich.console import Console
from rich.theme import Theme
from collections import defaultdict
from .env import env

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



def get_config() -> None:
    """
    Prende le impostazioni scelte dall'utente
    dal file di configurazione.

    Returns:
        None
    """
    global config_data

    config_path = Path(__file__).parent.parent / "config.toml"

    with open(config_path, 'r') as f:
        data = toml.load(f)

    config_data.clear()
    config_data.update(data)

    # Merge with default styles if missing
    if "style" not in config_data:
        config_data["style"] = DEFAULT_STYLE.copy()
    else:
        for key, value in DEFAULT_STYLE.items():
            if key not in config_data["style"]:
                config_data["style"][key] = value

    global console
    console = Console(theme=Theme(config_data["style"]), highlight=False)

    if env.is_wsl:
        config_data["player"]["path"] = env.wrap_path_for_wsl(config_data["player"]["path"])
        if "syncplay" in config_data:
            config_data["syncplay"]["path"] = f"/mnt/c/Windows/System32/cmd.exe /C '{config_data['syncplay']['path']}'"

    if "specials" not in config_data["general"]:
        config_data["general"]["specials"] = False
    if "complete_limit" not in config_data["player"]:
        config_data["player"]["complete_limit"] = 90
