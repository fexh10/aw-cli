# pyright: reportUnusedImport=false
from .provider import Provider

PROVIDERS_AVAILABLE = {
    "animeunity": ("aw_cli.providers.animeunity", "Animeunity"),
    "animeworld": ("aw_cli.providers.animeworld", "Animeworld"),
}

def create_provider(name: str) -> Provider:
    """
    Crea un'istanza del provider in base al nome.
    Usa importazione lazy per caricare solo il modulo necessario.

    Args:
        name (str): il nome del provider (es. 'animeunity', 'animeworld').

    Returns:
        Provider: l'istanza del provider creato.

    Raises:
        ValueError: se il nome del provider non è disponibile.
    """
    if name not in PROVIDERS_AVAILABLE:
        raise ValueError(f"Provider '{name}' non disponibile. Scegli tra: {list(PROVIDERS_AVAILABLE.keys())}")

    module_name, class_name = PROVIDERS_AVAILABLE[name]
    import importlib
    module = importlib.import_module(module_name)
    provider_class = getattr(module, class_name)
    return provider_class()

__all__ = [
    "Provider",
    "create_provider",
]
