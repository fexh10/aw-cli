from rich.console import Console
from rich.theme import Theme
from ..core.config import config

# Inizializza la console usando i colori predefiniti definiti nei defaults di config.py
# force_terminal=True assicura che vengano sempre generati i codici ANSI anche in pipe/test
console = Console(
    theme=Theme(config.data["style"]),
    highlight=False,
    force_terminal=True
)
