from pathlib import Path
from signal import signal, SIGINT
from .core.config import config
from .cli.setup_config import setup_config
from .cli.menus import ask_select_anime
from .arg_parser import args, parser

from .cli.handlers import (
    handle_watch_session,
    handle_get_anime_list,
    handle_background_reload,
    handle_background_fetch,
    handle_anime_removal,
    handle_show_info_flow,
    handle_episode_resolution,
    handle_download_flow,
)

from .providers import (
    LocalProvider,
    create_provider,
    Provider,
)
from .interface import Fzf
from .core.history import history

signal(SIGINT, lambda signum, frame: exit())

class CliApp:
    def __init__(self):
        self.provider: Provider | None = None
        self.fzf = Fzf()
        self.reload = True
        self.animelist = []

    def setup(self):
        # se il file di configurazione non esiste viene chiesto all'utente di fare il setup
        if getattr(args, 'start_config', False) or not config.path.exists():
            setup_config()

        config.load()
        history.load(str(Path(__file__).parent))

        is_offline = (getattr(args, 'action', 'search') == 'offline')

        if is_offline:
            self.provider = LocalProvider(config.download_path, history.get())
        else:
            self.provider = create_provider(config.data["provider"]["source"])

    def handle_search_flow(self):
        self._run_loop(hist=False, latest=False, offline=False, latest_filter="a")

    def handle_history_flow(self):
        self._run_loop(hist=True, latest=False, offline=False, latest_filter="a")

    def handle_latest_flow(self):
        self._run_loop(hist=False, latest=True, offline=False, latest_filter=getattr(args, 'filter', 'a'))

    def handle_offline_flow(self):
        self._run_loop(hist=True, latest=False, offline=True, latest_filter="a")

    def _run_loop(self, hist: bool, latest: bool, offline: bool, latest_filter: str):
        assert self.provider is not None
        while True:
            if self.reload:
                self.animelist = handle_get_anime_list(self.provider, hist, latest, offline, latest_filter)

            is_remove_requested = getattr(args, 'remove', False)
            history_flag = "r" if is_remove_requested else None

            handle_background_reload(self.provider, self.fzf, hist, offline, history_flag)

            anime = ask_select_anime(self.animelist, hist, latest, is_remove_requested)

            if handle_anime_removal(anime, history_flag):
                continue

            self.provider.info_anime(anime)

            is_info_enabled = getattr(args, 'info', False)
            is_downl_enabled = getattr(args, 'download', False)
            is_private_enabled = getattr(args, 'private', False)
            is_syncpl_enabled = getattr(args, 'syncpl', False)

            if handle_show_info_flow(anime, is_info_enabled):
                continue

            episodes, self.reload = handle_episode_resolution(
                anime, self.provider, hist, latest, is_downl_enabled, self.animelist
            )
            if episodes is None:
                continue

            episode = episodes[0]

            if handle_download_flow(anime, episodes, self.provider, is_downl_enabled):
                continue

            handle_background_fetch(self.provider, anime, offline)

            handle_watch_session(anime, episode, self.provider, offline, is_private_enabled, is_syncpl_enabled)

            self.reload = True

    def run(self):
        self.setup()

        flows = {
            'search': self.handle_search_flow,
            'history': self.handle_history_flow,
            'latest': self.handle_latest_flow,
            'offline': self.handle_offline_flow,
        }
        flow_method = flows.get(getattr(args, 'action', 'search'), self.handle_search_flow)
        flow_method()


def main():
    app = CliApp()
    app.run()


if __name__ == "__main__":
    main()
