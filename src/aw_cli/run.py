
from time import sleep
from pathlib import Path
from signal import signal, SIGINT
from concurrent.futures import ThreadPoolExecutor
from threading import Thread
from typing import Callable
from rich.prompt import FloatPrompt
from .core import (
    anilist,
    download,
)
from .core.config import config
from .cli.setup_config import setup_config
from .cli.menus import ask_search_query, ask_select_anime, ask_select_episodes, ask_show_info, list_anime_names
from .interface import console
from .core.env import env

from .providers import (
    Provider,
    LocalProvider,
    create_provider,
)
from .interface import Fzf, console
from .core.player import open_player
from .core.history import history
from .core.anime import Anime, AnimeStatus
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


def search_anime(provider: Provider) -> list[Anime]:
    """
    Dato in input un nome di un anime inserito dall'utente, restituisce una lista con gli URL degli anime
    relativi alla ricerca.

    Returns:
        list[Anime]: la lista con gli URL degli anime trovati
    """

    def check_search(s: str):
        if s == "exit":
            exit()
        result = provider.search(s)
        if len(result) != 0:
            return result

    console.clear()
    while True:
        query = ask_search_query()
        if res := check_search(query):
            return res
        console.print("La ricerca non ha prodotto risultati", style="error")
        sleep(1)
        console.clear()


def select_episodes(anime: Anime) -> list[Anime.Episode]:
    """
    Fa scegliere all'utente gli episodi dell'anime da guardare.

    Se l'anime ha solo un episodio, questo verrà riprodotto automaticamente.
    In caso contrario, l'utente può scegliere un episodio.

    Args:
        anime (Anime): l'anime di cui scegliere gli episodi.

    Returns:
        list[Anime.Episode]: La lista degli oggetti Episode selezionati.
    """
    console.clear()
    console.print(anime.name)
    # se contiene solo 1 ep sarà riprodotto automaticamente
    if len(anime.episodes()) == 1:
        return anime._episodes

    choices = list(reversed(anime.episodes()))
    res = ask_select_episodes(anime.name, choices, downl)
    return [anime.episode(num) for num in res]

def update_anilist(
    anime: Anime,
    episode: Anime.Episode,
    anilist_rating: float | None,
    drop: bool = False,
) -> None:
    """
    Procede ad aggiornare l'anime su AniList.
    Se l'episodio riprodotto è l'ultimo e
    l'utente ha scelto di votare gli anime,
    verrà chiesto il voto da dare.

    Args:
        anime (Anime): l'anime da aggiornare.
        episode (Anime.Episode): l'episodio da aggiornare.
        anilist_rating (float|None): il voto che l'utente ha assegnato all'anime.
        drop (bool, optional): True se l'utente decide di droppare l'anime, altrimenti False.
    """

    if anime.anilist_id == 0:
        console.print(
            "Impossibile aggiornare AniList: id anime non trovato!", style="error"
        )
        return

    rating = 0
    favorite = False
    status_list = "CURRENT" if not drop else "DROPPED"
    # se ho finito di vedere l'anime o lo stato è dropped
    if (
        episode.numeric() == int(anime.last_ep) and anime.status == AnimeStatus.FINISHED
    ) or status_list == "DROPPED":
        if status_list == "CURRENT":
            status_list = "COMPLETED"

        # chiedo di votare
        # chiedo di votare
        if config.data["anilist"]["rating"]:
            prompt_text = "Inserisci un voto per l'anime" + (
                f" (voto corrente: {anilist_rating})" if anilist_rating else ""
            )
            while True:
                try:
                    rating = FloatPrompt.ask(prompt_text, console=console)
                    if rating < 0:
                        raise ValueError
                    break
                except ValueError:
                    console.print("Seleziona una risposta valida!", style="error")

        # chiedo di mettere tra i preferiti
        if config.data["anilist"]["favorite"] and status_list == "COMPLETED":
            console.clear()
            console.print(
                f"Riproduco {anime.name} Ep. {anime.last_ep}", style="info"
            )
            favorite = (
                Fzf().run(["sì", "no"], "Mettere l'anime tra i preferiti? ") == "sì"
            )

    Thread(
        target=anilist.update_anilist,
        args=(
            config.data["anilist"]["token"],
            anime.anilist_id,
            episode.numeric(),
            status_list,
            rating,
            favorite,
        ),
    ).start()


def watch_episode(
    anime: Anime, episode: Anime.Episode, provider: Provider
) -> None:
    """
    Riproduce l'episodio dell'anime e gestisce gli aggiornamenti di stato.
    Se un episodio è già stato scaricato, viene riprodotto dal file scaricato.
    Altrimenti, viene riprodotto in streaming.

    Args:
        anime (Anime): l'anime di cui riprodurre l'episodio.
        episode (Anime.Episode): l'episodio da riprodurre.
        provider (Provider): il provider da cui prendere il link dell'episodio.
    """
    anilist_rating = None
    if not (offline or private) and "anilist" in config.data:
        executor = ThreadPoolExecutor(max_workers=1)
        anilist_rating = executor.submit(
            anilist.get_anime_private_rating,
            config.data["anilist"]["token"],
            config.data["anilist"]["user_id"],
            anime.anilist_id,
        )

    # se il video è già stato scaricato lo riproduco invece di farlo in streaming
    local_file = download.get_episode_path(anime, episode, create=False)

    if local_file.exists():
        ep_url = str(local_file) if env.is_android else "file://" + str(local_file)
    else:
        ep_url = provider.episode_link(anime, episode)

    console.clear()
    console.print(f"Riproduco {episode}...", style="info")
    completed, progress = open_player(ep_url, str(episode), episode.progress, args.syncpl)

    if not private:
        episode.set_progress(progress)
        if completed:
            episode.mark_completed()
            # update watchlist anilist se ho fatto l'accesso
            if anilist_rating:
                update_anilist(anime, episode, anilist_rating.result())

        anime.curr_ep = episode.num
        history.update(anime, episode)





def remove_from_history(anime: Anime) -> None:
    """
    Rimuove l'anime selezionato dalla cronologia
    e stampa un menu di scelta per l'utente.

    Args:
        number (int): il numero dell'anime in lista da rimuovere.

    Returns:
        None.
    """

    if (
        Fzf().run(
            ["sì", "no"],
            f"Si è sicuri di voler rimuovere {anime.name} dalla cronologia? ",
        )
        == "no"
    ):
        return

    if (
        "anilist" in config.data
        and config.data["anilist"]["drop"]
        and Fzf().run(["sì", "no"], f"Droppare {anime.name} su AniList? ") == "sì"
    ):
        if anime.anilist_id == 0:
            console.print(
                "Impossibile droppare su AniList: id anime non trovato!", style="error"
            )
            sleep(1)
        else:
            rating = anilist.get_anime_private_rating(
                config.data["anilist"]["token"],
                config.data["anilist"]["user_id"],
                anime.anilist_id,
            )
            update_anilist(anime, anime.episode(anime.curr_ep), rating, drop=True)

    history.remove(anime)

    console.clear()
    if Fzf().run(["esci", "continua"]) == "esci":
        exit()


def create_ep_menu(
    anime: Anime, episode: Anime.Episode
) -> dict[str, Callable[[], Anime.Episode | str]]:
    """
    Genera il menu di riproduzione di un episodio,
    con le azioni disponibili in base allo stato dell'anime e dell'episodio.

    Args:
        anime (Anime): l'anime di cui è stato riprodotto l'episodio.
        episode (Anime.Episode): l'episodio riprodotto.

    Returns:
        dict[str, Callable[[], Anime.Episode|str]]: un dizionario che
            associa a ogni azione disponibile una funzione che la esegue.
    """
    actions = {
        "esci": exit,
        "indietro": lambda: "break",
        "seleziona": lambda: select_episodes(anime)[0],
        "antecedente": episode.prev,
        "riguarda": lambda: episode,
        "prossimo": episode.next,
    }

    conditions = {
        "seleziona": len(anime.episodes()) > 1 or anime.last_ep != "1",
        "antecedente": episode.has_prev(),
        "prossimo": episode.has_next(),
    }

    return {k: v for k, v in actions.items() if conditions.get(k, True)}


def main():
    global history

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
            if offline:
                animelist = provider.search("")  # Uses offline provider
            elif hist:
                animelist = history.get()
            elif latest:
                animelist = provider.latest(args.latest)
            else:
                animelist = search_anime(provider)

            if not animelist:
                message = "Cronologia vuota!" if hist else "Nessun anime trovato!"
                console.print(message, style="error")
                exit()

        if hist and history.has_ongoing() and args.history != "r" and not offline:

            def background_reload():
                history.reload(provider.latest())
                animelist_updated = history.get()
                fzf.reload(list_anime_names(animelist_updated))

            Thread(target=background_reload, daemon=True).start()

        anime = ask_select_anime(animelist, hist, latest, args.history == "r")

        if args.history == "r":
            remove_from_history(anime)
            continue

        provider.info_anime(anime)

        if info and ask_show_info(anime) == "indietro":
            continue

        if len(anime.episodes()) == 0:
            provider.episodes(anime)

        if len(anime.episodes()) == 0:
            console.print(
                "Eh, volevi! L'anime non è ancora stato rilasciato", style="error"
            )
            sleep(1)
            reload = False
            continue

        if hist and anime.episode(anime.curr_ep).is_completed():
            ep_corrente = anime.episode(anime.curr_ep)
            if not ep_corrente.has_next():
                provider.episodes(anime)

            if not ep_corrente.has_next():
                console.print(
                    f"L'episodio {ep_corrente.numeric() + 1} di {anime.name} non è ancora stato rilasciato!",
                    style="error",
                )
                sleep(1)
                if len(animelist) == 1:
                    exit()
                continue

            episodes = [ep_corrente.next()]
        elif latest or hist:
            episodes = [anime.episode(anime.curr_ep)]
        else:
            episodes = select_episodes(anime)

        episode = episodes[0]

        if downl:
            download.episodes(anime, episodes, provider)

            anime.curr_ep = episode.num
            if not any(anime == a for a in history.get()):
                history.update(anime, episode)

            answer = Fzf().run(["esci", "indietro", "guarda"])
            if answer == "esci":
                exit()
            if answer == "indietro":
                continue

        needs_fetch = not anime.has_all_episodes()
        if needs_fetch and not offline:
            Thread(target=provider.episodes, args=(anime,), daemon=True).start()

        while True:
            watch_episode(anime, episode, provider)

            # menù che si visualizza dopo aver finito la riproduzione
            menu_actions = create_ep_menu(anime, episode)

            res = menu_actions[Fzf().run(list(menu_actions.keys()))]()
            if isinstance(res, Anime.Episode):
                episode = res
            elif res == "break":
                break
        reload = True




if __name__ == "__main__":
    main()
