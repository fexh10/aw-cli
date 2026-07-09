from time import sleep
from typing import Callable
from rich.prompt import Prompt, FloatPrompt
from ..core.anime import Anime
from ..interface import Fzf, console


def ask_search_query() -> str:
    """
    Richiede all'utente il nome dell'anime da cercare.

    Returns:
        str: La query inserita dall'utente.
    """
    console.clear()
    return Prompt.ask("Cerca un anime (o digita 'exit' per uscire)", console=console)


def ask_select_anime(animelist: list[Anime], hist: bool = False, latest: bool = False, remove: bool = False) -> Anime:
    """
    Dato in input una lista di anime, permette all'utente di sceglierne uno.

    Args:
        animelist (list[Anime]): La lista di anime tra cui scegliere.
        remove (bool): Se True, permette all'utente di scegliere di rimuovere l'anime.

    Returns:
        Anime: L'anime selezionato dall'utente.
    """
    console.clear()
    prompt = "Scegli un anime: " if not remove else "Rimuovi un anime: "
    selected_anime = Fzf().run(list_anime_names(animelist, hist, latest), prompt)
    selected = int(selected_anime.split("  ")[0]) - 1
    return animelist[selected]


def ask_select_episodes(anime_name: str, choices: list[str], downl: bool = False) -> list[str]:
    """
    Mostra un menu per far scegliere all'utente uno o più episodi da guardare o scaricare.

    Args:
        anime_name (str): Il nome dell'anime.
        choices (list[str]): Lista di episodi disponibili tra cui scegliere.
        downl (bool): Se True, permette selezioni multiple.

    Returns:
        list[str]: La lista dei numeri di episodio selezionati sotto forma di stringhe.
    """
    console.clear()
    console.print(anime_name)

    prompt = "Scegli episodi: " if downl else "Scegli un episodio: "

    res = Fzf().run(
        choices,
        prompt=prompt,
        multi=downl,
        filter=downl,
    ).split("\n")

    return res


def ask_show_info(anime: Anime) -> str:
    """
    Mostra le informazioni dell'anime all'utente.

    Args:
        anime (Anime): l'anime di cui mostrare le informazioni.

    Returns:
        str: 'indietro' se l'utente vuole tornare indietro, 'guardare' altrimenti.
    """
    console.clear()
    console.print(anime)
    return Fzf().run(["indietro", "guardare"])


def ask_post_download(anime: Anime, episode: Anime.Episode) -> str:
    """
    Mostra le informazioni dell'anime all'utente.

    Args:
        anime (Anime): l'anime di cui mostrare le informazioni.

    Returns:
        str: 'esci', 'indietro' o 'guarda'.
    """
    console.clear()
    console.print(f"Scaricato {anime} Ep. {episode}")
    return Fzf().run(["esci", "indietro", "guarda"])


def ask_confirm_remove(anime_name: str) -> bool:
    """Chiede conferma all'utente prima di rimuovere un anime dalla cronologia."""
    return Fzf().run(
        ["sì", "no"],
        f"Si è sicuri di voler rimuovere {anime_name} dalla cronologia? ",
    ) == "sì"


def ask_confirm_drop(anime_name: str) -> bool:
    """Chiede all'utente se desidera droppare l'anime su AniList."""
    return Fzf().run(
        ["sì", "no"],
        f"Droppare {anime_name} su AniList? "
    ) == "sì"


def ask_post_remove() -> str:
    """Mostra le opzioni post-rimozione dalla cronologia."""
    return Fzf().run(["esci", "continua"])


def ask_anilist_rating(current_rating: float | None = None) -> float:
    """Richiede all'utente il voto da assegnare all'anime per AniList."""
    prompt_text = "Inserisci un voto per l'anime" + (
        f" (voto corrente: {current_rating})" if current_rating else ""
    )
    while True:
        try:
            rating = FloatPrompt.ask(prompt_text, console=console)
            if rating < 0:
                raise ValueError
            return rating
        except ValueError:
            console.print("Seleziona una risposta valida!", style="error")


def ask_anilist_favorite(anime_name: str, episode_num: str) -> bool:
    """Chiede all'utente se desidera inserire l'anime tra i preferiti di AniList."""
    console.clear()
    console.print(f"Riproduco {anime_name} Ep. {episode_num}", style="info")
    return Fzf().run(["sì", "no"], "Mettere l'anime tra i preferiti? ") == "sì"


def ask_post_watch_action(actions: list[str]) -> str:
    """Mostra il menu delle azioni disponibili dopo la visione di un episodio."""
    return Fzf().run(actions)


# ==========================================
# FUNZIONI UTILITARIE (Utility Functions)
# ==========================================

def list_anime_names(animelist: list[Anime], hist: bool = False, latest: bool = False) -> list[str]:
    """
    Genera una lista di stringhe formattate con i
    nomi degli anime presenti nella lista desiderata.

    Args:
        animelist (list[Anime]): Una lista Anime.

    Return:
        list[str]: lista di stringhe formattate.
    """
    names = []
    for i, a in reversed(list(enumerate(animelist))):
        style_name = "success"
        if (
            hist
            and a.curr_ep == a.last_ep
            and (not a.has_episode(a.curr_ep) or a.episode(a.curr_ep).is_completed())
        ):
            style_name = "error"

        name = f"[{style_name}]{i + 1}  [/]"

        if hist:
            name += f"{a.name} [Ep {a.curr_ep}/{a.info['Episodi']}]"
        elif latest:
            name += f"{a.name} [Ep {a.curr_ep}]"
        else:
            name += f"{a.name}"
        names.append(name)

    return names
