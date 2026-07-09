import toml
from pathlib import Path
from .env import env


class Config:
    def __init__(self):
        self._defaults = {
            "player": {
                "type": "android" if env.is_android else "mpv",
                "path": None,
                "complete_limit": 90,
            },
            "general": {
                "specials": False,
                "parallel-downloads": 3,
            },
            "download": {
                "path": None,
            },
            "anilist": {
                "token": None,
                "user_id": None,
                "rating": False,
                "favorite": False,
                "drop": False,
            },
            "style": {
                "error": "bold red",
                "prompt": "bold light_sky_blue3",
                "warning": "bold yellow",
                "success": "bold green",
                "info": "bright_yellow",
                "highlight": "cyan",
                "general": "white"
            },
            "syncplay": {
                "path": None,
            },
            "provider": {
                "source": "animeunity"
            }
        }
        self.data = {}
        self.on_load_callbacks = []
        self._reset_to_defaults()
        self.path = Path(__file__).parent.parent / "config.toml"

    def _reset_to_defaults(self) -> None:
        self.data.clear()
        for key, val in self._defaults.items():
            self.data[key] = val.copy()

    def load(self) -> None:
        """
        Prende le impostazioni scelte dall'utente dal file di configurazione
        e le unisce ai valori di default.
        """
        if not self.path.exists():
            for cb in self.on_load_callbacks:
                cb(self)
            return

        with open(self.path, 'r') as f:
            loaded_data = toml.load(f)

        # Ripristiniamo i default e facciamo l'unione sezione per sezione
        self._reset_to_defaults()
        for section, default_values in self._defaults.items():
            loaded_section = loaded_data.get(section, {})
            self.data[section] = {**default_values, **loaded_section}

        for cb in self.on_load_callbacks:
            cb(self)

    @property
    def player_path(self) -> str | None:
        """
        Ritorna il percorso del player, applicando i wrapper WSL a runtime se necessario.
        I dati in self.data rimangono sempre puri (identici al TOML su disco).
        """
        return env.wrap_path_for_wsl(self.data["player"]["path"])

    @property
    def syncplay_path(self) -> str | None:
        """
        Ritorna il percorso di Syncplay, applicando i wrapper WSL a runtime se necessario.
        I dati in self.data rimangono sempre puri (identici al TOML su disco).
        """
        return env.wrap_path_for_wsl(self.data["syncplay"]["path"], syncplay=True)

    @property
    def download_path(self) -> Path:
        """
        Ritorna il percorso di download configurato dall'utente,
        oppure il default specifico per la piattaforma corrente (Android vs Desktop).
        """
        user_path = self.data.get("download", {}).get("path")
        if user_path:
            return Path(user_path)

        if env.is_android:
            return Path("/sdcard/Movies/Anime")
        return Path.home() / "Videos/Anime"

    def save(self, data: dict) -> None:
        """
        Salva le impostazioni nel file di configurazione.
        Dopo il salvataggio ricarica i dati in memoria per allineare l'istanza.
        """
        with open(self.path, 'w') as f:
            toml.dump(data, f)
        self.load()


# Istanza unica (Singleton) utilizzata in tutta l'applicazione
config = Config()

