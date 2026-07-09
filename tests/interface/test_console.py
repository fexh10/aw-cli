from aw_cli.core.config import config
from aw_cli.interface import console

def test_console_theme_updates_with_config():
    # Salviamo lo stile originale per ripristinarlo a fine test
    original_style = config.data["style"].copy()

    try:
        # Cambiamo temporaneamente lo stile dell'errore e il general
        config.data["style"]["error"] = "blue"
        config.data["style"]["general"] = "green"

        # Invochiamo il caricamento o i callback registrati su config
        for cb in config.on_load_callbacks:
            cb(config)

        # Verifichiamo che il tema della console si sia effettivamente aggiornato
        style_in_theme = console.get_style("error")
        assert style_in_theme.color.name == "blue"

        # Verifichiamo lo stile generale di default della console
        assert console.style == "green"

    finally:
        # Ripristiniamo lo stile iniziale
        config.data["style"] = original_style
        for cb in config.on_load_callbacks:
            cb(config)
