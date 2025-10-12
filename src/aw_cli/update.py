import subprocess 
import shutil
from . import utilities as ut

REPO_URL = "git+https://github.com/fexh10/aw-cli.git@branch-name"

# Configurazione minimalista dei comandi per ogni tool
TOOLS = {
    "uv": {
        "list": ["uv", "tool", "list"],
        "update": ["uv", "tool", "update", "aw-cli"],
        "install_git": ["uv", "tool", "install", REPO_URL, "--force"]
    },
    "pipx": {
        "list": ["pipx", "list"],
        "update": ["pipx", "update", "aw-cli"],
        "install_git": ["pipx", "install", REPO_URL, "--force"]
    },
    "pip": {
        "list": ["pip", "list"],
        "update": ["pip", "install", "aw-cli", "--upgrade"],
        "install_git": ["pip", "install", REPO_URL, "--force-reinstall"]
    }
}


def check_installation_method() -> str | None:
    """
    Controlla il metodo di installazione dello script.

    Returns:
        str | None: il nome del tool rilevato, o None se non trovato.
    """
    for tool_name, commands in TOOLS.items():
        if shutil.which(tool_name):
            result = subprocess.run(commands["list"], capture_output=True)
            if result.returncode == 0 and "aw-cli" in result.stdout.decode():
                return tool_name
    return None
        
def update(branch: str) -> None:
    """
    Aggiorna lo script in base al metodo di installazione.

    Args:
        branch (str): il branch da cui aggiornare lo script. Se la stringa è vuota, aggiorna all'ultima versione stabile.
    """
    tool = check_installation_method()
    if not tool:
        ut.my_print("Non è stato possibile trovare un metodo di installazione valido per aggiornare aw-cli", color="rosso")
        return

    command = TOOLS[tool]["install_git"] if branch else TOOLS[tool]["update"]
    command = [cmd.replace("branch-name", branch) for cmd in command] # sostituisco "branch-name" con il nome del branch
    subprocess.run(command)