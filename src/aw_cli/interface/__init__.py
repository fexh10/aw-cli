from rich.theme import Theme
from ..core.config import config
from .fzf import Fzf
from .console import console

_theme_pushed = False

def _update_console_theme(cfg) -> None:
    """Callback che aggiorna dinamicamente il tema e lo stile di default della console."""
    global _theme_pushed
    if _theme_pushed:
        console.pop_theme()
    console.push_theme(Theme(cfg.data["style"]), inherit=False)
    _theme_pushed = True
    
    # Imposta lo stile di default della console sul colore "general"
    if "general" in cfg.data["style"]:
        console.style = cfg.data["style"]["general"]

# Si registra su config per ricevere aggiornamenti automatici ad ogni load() o save()
config.on_load_callbacks.append(_update_console_theme)

__all__ = ["Fzf", "console"]
