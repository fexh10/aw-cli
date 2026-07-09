from pathlib import Path
from signal import signal, SIGINT
from .core.config import config
from .cli.setup_config import setup_config
from .cli.menus import ask_select_anime

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
)
from .interface import Fzf
from .core.history import history
from .arg_parser import (
    args,
    info,
    downl,
    latest,
    offline,
    private,
    hist,
)

signal(SIGINT, lambda signum, frame: exit())

def main():
    # se il file di configurazione non esiste viene chiesto all'utente di fare il setup
    if args.start_config or not config.path.exists():
        setup_config()

    config.load()
    history.load(str(Path(__file__).parent))

    if offline:
        provider = LocalProvider(config.download_path, history.get())
    else:
        provider = create_provider(config.data["provider"]["source"])

    fzf = Fzf()
    reload = True
    animelist = []
    while True:
        if reload:
            animelist = handle_get_anime_list(provider, hist, latest, offline, args.latest)

        handle_background_reload(provider, fzf, hist, offline, args.history)

        anime = ask_select_anime(animelist, hist, latest, args.history == "r")

        if handle_anime_removal(anime, args.history):
            continue

        provider.info_anime(anime)

        if handle_show_info_flow(anime, info):
            continue

        episodes, reload = handle_episode_resolution(anime, provider, hist, latest, downl, animelist)
        if episodes is None:
            continue

        episode = episodes[0]

        if handle_download_flow(anime, episodes, provider, downl):
            continue

        handle_background_fetch(provider, anime, offline)

        handle_watch_session(anime, episode, provider, offline, private, args.syncpl)

        reload = True


if __name__ == "__main__":
    main()
