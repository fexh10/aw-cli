from pathlib import Path
from signal import signal, SIGINT
from .core.config import config
from .cli.setup_config import setup_config
from .cli.menus import (
    ask_select_anime,
    ask_show_info,
)

from .cli.handlers import (
    handle_remove_from_history,
    handle_watch_session,
    handle_get_anime_list,
    handle_resolve_episodes,
    handle_download,
    handle_background_reload,
    handle_background_fetch,
)

from .providers import (
    LocalProvider,
    create_provider,
)
from .interface import Fzf, console
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
            if not animelist:
                message = "Cronologia vuota!" if hist else "Nessun anime trovato!"
                console.print(message, style="error")
                exit()

        if hist and history.has_ongoing() and args.history != "r" and not offline:
            handle_background_reload(provider, fzf)

        anime = ask_select_anime(animelist, hist, latest, args.history == "r")

        if args.history == "r":
            handle_remove_from_history(anime)
            continue

        provider.info_anime(anime)

        if info and ask_show_info(anime) == "indietro":
            continue

        episodes, reload_list = handle_resolve_episodes(anime, provider, hist, latest, downl)
        if not episodes:
            if not reload_list:
                reload = False
            else:
                if len(animelist) == 1:
                    exit()
            continue

        episode = episodes[0]

        if downl:
            answer = handle_download(anime, episodes, provider)
            if answer == "esci":
                exit()
            if answer == "indietro":
                continue

        needs_fetch = not anime.has_all_episodes()
        if needs_fetch and not offline:
            handle_background_fetch(provider, anime)

        handle_watch_session(anime, episode, provider, offline, private, args.syncpl)

        reload = True


if __name__ == "__main__":
    main()
