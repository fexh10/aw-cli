from typing import Callable
from aw_cli.core.anime import AnimeStatus
from time import sleep
from threading import Thread
from .menus import (
    ask_confirm_remove,
    ask_confirm_drop,
    ask_post_remove,
    ask_anilist_rating,
    ask_anilist_favorite,
    ask_post_watch_action,
    ask_search_query,
    ask_select_episodes,
    ask_post_download,
    list_anime_names,
    ask_show_info,
)
from ..interface import Fzf
from ..core import anilist
from ..core.anime import Anime
from ..providers import Provider
from ..core.config import config
from ..core.player import open_player
from ..core import download
from ..core.history import history
from ..interface.console import console
from concurrent.futures import ThreadPoolExecutor
from ..core.env import env


def handle_update_anilist(
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
        if config.data["anilist"]["rating"]:
            rating = ask_anilist_rating(anilist_rating)

        # chiedo di mettere tra i preferiti
        if config.data["anilist"]["favorite"] and status_list == "COMPLETED":
            favorite = ask_anilist_favorite(anime.name, anime.last_ep)

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


def handle_remove_from_history(anime: Anime) -> None:
    """
    Rimuove l'anime selezionato dalla cronologia
    e stampa un menu di scelta per l'utente.

    Args:
        anime (Anime): l'anime da rimuovere dalla cronologia.
    """
    if not ask_confirm_remove(anime.name):
        return

    if (
        "anilist" in config.data
        and config.data["anilist"]["drop"]
        and ask_confirm_drop(anime.name)
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
            handle_update_anilist(anime, anime.episode(anime.curr_ep), rating, drop=True)

    history.remove(anime)

    console.clear()
    if ask_post_remove() == "esci":
        exit()


def handle_watch_episode(
    anime: Anime, episode: Anime.Episode, provider: Provider, offline: bool = False, private: bool = False, syncpl: bool = False
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
    completed, progress = open_player(ep_url, str(episode), episode.progress, syncpl)

    if not private:
        episode.set_progress(progress)
        if completed:
            episode.mark_completed()
            # update watchlist anilist se ho fatto l'accesso
            if anilist_rating:
                handle_update_anilist(anime, episode, anilist_rating.result())

        anime.curr_ep = episode.num
        history.update(anime, episode)


def handle_watch_session(anime, episode, provider, offline, private, syncpl):
    """Gestisce il ciclo di visione degli episodi e il menu post-riproduzione."""
    while True:
        handle_watch_episode(anime, episode, provider, offline, private, syncpl)

        menu_actions = create_ep_menu(anime, episode)
        action_key = ask_post_watch_action(list(menu_actions.keys()))
        res = menu_actions[action_key]()

        if isinstance(res, Anime.Episode):
            episode = res
        elif res == "break":
            break


def handle_search(provider: Provider) -> list[Anime]:
    """Gestisce il ciclo di ricerca dell'anime contattando il provider e validando i risultati."""
    while True:
        query = ask_search_query()
        if query == "exit":
            exit()
        result = provider.search(query)
        if len(result) != 0:
            return result
        console.print("La ricerca non ha prodotto risultati", style="error")
        sleep(1)


def handle_get_anime_list(
    provider: Provider,
    hist: bool,
    latest: bool,
    offline: bool,
    latest_filter: str = "all"
) -> list[Anime]:
    """Recupera la lista di anime appropriata in base ai parametri e alla modalità."""
    if offline:
        animelist = provider.search("")
    elif hist:
        animelist = history.get()
    elif latest:
        animelist = provider.latest(latest_filter)
    else:
        animelist = handle_search(provider)

    if not animelist:
        message = "Cronologia vuota!" if hist else "Nessun anime trovato!"
        console.print(message, style="error")
        exit()
    return animelist


def handle_resolve_episodes(
    anime: Anime,
    provider: Provider,
    hist: bool,
    latest: bool,
    downl: bool
) -> tuple[list[Anime.Episode], bool]:
    """
    Risolve e seleziona gli episodi da riprodurre o scaricare.
    Ritorna una tupla (lista_episodi, reload_animelist).
    """
    if len(anime.episodes()) == 0:
        provider.episodes(anime)

    if len(anime.episodes()) == 0:
        console.print(
            "Eh, volevi! L'anime non è ancora stato rilasciato", style="error"
        )
        sleep(1)
        return [], False

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
            return [], True

        return [ep_corrente.next()], True
    elif latest or hist:
        return [anime.episode(anime.curr_ep)], True
    else:
        # Se c'è un solo episodio lo carichiamo automaticamente
        if len(anime.episodes()) == 1:
            return anime._episodes, True

        choices = list(reversed(anime.episodes()))
        res = ask_select_episodes(anime.name, choices, downl)
        return [anime.episode(num) for num in res], True


def handle_download(anime: Anime, episodes: list[Anime.Episode], provider: Provider) -> str:
    """Gestisce il download degli episodi selezionati, aggiorna la cronologia e mostra il menu finale."""
    download.episodes(anime, episodes, provider)

    episode = episodes[0]
    anime.curr_ep = episode.num
    if not any(anime == a for a in history.get()):
        history.update(anime, episode)

    return ask_post_download(anime, episode)


def handle_background_reload(provider: Provider, fzf: Fzf, hist: bool, offline: bool, history_flag: str | None) -> None:
    """Ricarica in background le ultime release per aggiornare la lista animelist in fzf se necessario."""
    if not (hist and history.has_ongoing() and history_flag != "r" and not offline):
        return

    def background_reload():
        history.reload(provider.latest())
        animelist_updated = history.get()
        fzf.reload(list_anime_names(animelist_updated, hist=True))

    Thread(target=background_reload, daemon=True).start()


def handle_background_fetch(provider: Provider, anime: Anime, offline: bool) -> None:
    """Avvia il fetch in background di tutti gli episodi per l'anime selezionato se necessario."""
    needs_fetch = not anime.has_all_episodes()
    if needs_fetch and not offline:
        Thread(target=provider.episodes, args=(anime,), daemon=True).start()


def handle_anime_removal(anime: Anime, history_flag: str | None) -> bool:
    """Se richiesto dai flag, rimuove l'anime dalla cronologia e ritorna True per indicare che si deve ricominciare il ciclo."""
    if history_flag == "r":
        handle_remove_from_history(anime)
        return True
    return False


def handle_show_info_flow(anime: Anime, info_enabled: bool) -> bool:
    """Mostra le informazioni dell'anime se abilitato e ritorna True se l'utente sceglie di tornare indietro."""
    if info_enabled and ask_show_info(anime) == "indietro":
        return True
    return False


def handle_episode_resolution(
    anime: Anime,
    provider: Provider,
    hist: bool,
    latest: bool,
    downl: bool,
    animelist: list[Anime]
) -> tuple[list[Anime.Episode] | None, bool]:
    """
    Risolve gli episodi dell'anime. In caso di errore o mancato rilascio, decide se
    ricaricare la lista anime, uscire dal programma o semplicemente continuare,
    ritornando (episodes, reload_flag).
    """
    episodes, reload_list = handle_resolve_episodes(anime, provider, hist, latest, downl)
    if not episodes:
        if reload_list and len(animelist) == 1:
            exit()
        return None, reload_list
    return episodes, True


def handle_download_flow(
    anime: Anime,
    episodes: list[Anime.Episode],
    provider: Provider,
    download_enabled: bool
) -> bool:
    """Gestisce il flusso di download se abilitato. Ritorna True se l'utente vuole tornare indietro."""
    if not download_enabled:
        return False
    answer = handle_download(anime, episodes, provider)
    if answer == "esci":
        exit()
    return answer == "indietro"



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
        "seleziona": lambda: anime.episode(ask_select_episodes(anime.name, list(reversed(anime.episodes())))[0]),
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
