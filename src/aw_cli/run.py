import re
import shutil
import subprocess
from time import sleep
from pathlib import Path
from signal import signal, SIGINT
from concurrent.futures import ThreadPoolExecutor
from threading import Thread
from rich.prompt import Prompt, FloatPrompt
from . import (
    anilist,
    download,
    providers,
    utilities as ut,
)
from .history import History
from .anime import Anime, AnimeStatus
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


def search_anime(provider: providers.Provider) -> list[Anime]:
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

    ut.console.clear()
    while True:
        query = Prompt.ask("Cerca un anime", console=ut.console)
        if res := check_search(query):
            return res
        ut.console.print("La ricerca non ha prodotto risultati", style="error")
        sleep(1)
        ut.console.clear()

def select_episodes(anime: Anime) -> list[Anime.Episode]:
    """
    Fa scegliere all'utente gli episodi dell'anime da guardare.

    Se l'anime ha solo un episodio, questo verrà riprodotto automaticamente.
    In caso contrario, l'utente può scegliere un episodio.

    Args:
        anime (Anime): l'anime di cui scegliere gli episodi.

    Returns:
        str: il numero dell'episodio da riprodurre.
    """


    ut.console.clear()
    ut.console.print(anime.name)
    #se contiene solo 1 ep sarà riprodotto automaticamente
    if len(anime.episodes()) == 1:
        return anime._episodes

    res = ut.fzf(list(reversed(anime.episodes())), "Scegli un episodio: ", multi=downl).split("\n")
    return [anime.episode(num) for num in res]

def open_syncplay(ep_url: str, ep_name: str, progress: int) -> tuple[bool, int]:
    """
    Avvia Syncplay.

    Args:
        ep_url (str): l'URL dell'episodio da riprodurre.
        ep_name (str): il nome dell'episodio.
        progress (int): il progresso dell'episodio.

    Returns:
        bool: True se l'episodio è stato riprodotto completamente, altrimenti False.
        int: il progresso dell'episodio.
    """

    if "syncplay" not in ut.config_data:
        ut.console.print("Aggiornare il path di syncplay nella configurazione tramite: aw-cli -a", style="error")
        exit()


    args = f'''--force-media-title="{ep_name}" --start="{progress}" --fullscreen --keep-open'''
    if ut.config_data.get("player", {}).get("type") == "vlc":
        args = f'''--meta-title "{ep_name}" --start-time="{progress}" --fullscreen'''

    try:
        command = f'''{ut.config_data["syncplay"]["path"]} -d --language it "{ep_url}" -- {args}'''
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=False)
        out = result.stdout
    except UnicodeDecodeError:
        out = ""

    duration_match = re.findall(r'duration(?:-change)?"?: (\d+)\.?[\d]*', out)
    progress_match = re.findall(r'pos(?:ition"?)?:? (\d+).?\d+', out)
    if not duration_match:
        ut.console.print("Errore, impossibile leggere l'output di Syncplay!", style="error")
        return False, 0

    duration = max(map(int, duration_match))
    progress_match = list(filter(lambda x: x>0, map(int, progress_match)))
    progress = progress_match[-1] if progress_match else 0

    return progress*100// duration >= complete_limit if duration > 0 else False, progress

def open_mpv(ep_url: str, ep_name: str, progress: int) -> tuple[bool, int]:
    """
    Apre MPV per riprodurre il video.

    Args:
        ep_url (str): il link del video o il percorso del file.
        ep_name (str): il nome del video.
        progress (int): il progresso dell'episodio.

    Returns:
        bool: True se l'episodio è stato riprodotto completamente, altrimenti False.
        int: il progresso dell'episodio.
    """


    if (ut.os_name == "Android"):
        subprocess.run(f'am start --user 0 -a android.intent.action.VIEW -d "{ep_url}" -n is.xyz.mpv/.MPVActivity', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True, 0

    command = f'''{ut.config_data["player"]["path"]} "{ep_url}" --force-media-title="{ep_name}" --start="{progress}" --fullscreen --keep-open'''
    result = subprocess.run(command, shell=True, capture_output=True, text=True, check=False)
    out = result.stdout

    res = re.findall(r'(\d+):(\d+):(\d+) / [\d:]+ \((\d+)%\)', out)[-1]
    progress = (int(res[0]) * 3600) + (int(res[1]) * 60) + int(res[2])

    return int(res[3]) >= complete_limit, progress

def open_vlc(ep_url: str, ep_name: str, progress: int) -> tuple[bool, int]:
    """
    Apre VLC per riprodurre il video.

    Args:
        ep_url (str): il link del video o il percorso del file.
        ep_name (str): il nome del video.
        progress (int): il progresso dell'episodio.

    Returns:
        bool: True se l'episodio è stato riprodotto completamente, altrimenti False.
        int: il progresso dell'episodio.
    """

    if ut.os_name == "Android":
        subprocess.run(f'am start --user 0 -a android.intent.action.VIEW -d "{ep_url}" -n org.videolan.vlc/.StartActivity -e "title" "{ep_name}"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True, 0

    subprocess.run(f'{ut.config_data["player"]["path"]} "{ep_url}" --meta-title "{ep_name}" --start-time="{progress}" --fullscreen', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # se il file di configurazione di VLC esiste, prendo la posizione dell'ultimo episodio riprodotto
    progress = 0
    vlc_config_path = Path.home() / ".config/vlc/vlc-qt-interface.conf" # Linux
    if vlc_config_path.exists():
        with open(vlc_config_path, "r") as file:
            config = [line.strip() for line in file.readlines()]
            index = config.index("[RecentsMRL]")
            urls = config[index + 1].split("=")[1].split(", ")
            positions = config[index + 2].split("=")[1].split(", ")
        progress = int(positions[urls.index(ep_url)]) // 1000 if ep_url in urls else 0

    # Non informazioni sulla durata: suppongo che sia completato
    return True, progress

def update_anilist(anime: Anime, episode: Anime.Episode, anilist_rating: float|None, drop: bool = False) -> None:
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
        ut.console.print("Impossibile aggiornare AniList: id anime non trovato!", style="error")
        return

    rating = 0
    favorite = False
    status_list = 'CURRENT' if not drop else 'DROPPED'
    #se ho finito di vedere l'anime o lo stato è dropped
    if (episode.numeric() == int(anime.last_ep) and anime.status == AnimeStatus.FINISHED) or status_list == 'DROPPED':
        if status_list == 'CURRENT':
            status_list = 'COMPLETED'

        #chiedo di votare
        #chiedo di votare
        if ut.config_data["anilist"]["rating"]:
            prompt_text = "Inserisci un voto per l'anime" + (f" (voto corrente: {anilist_rating})" if anilist_rating else "")
            while True:
                try:
                    rating = FloatPrompt.ask(prompt_text, console=ut.console)
                    if rating < 0: raise ValueError
                    break
                except ValueError:
                    ut.console.print("Seleziona una risposta valida!", style="error")

        #chiedo di mettere tra i preferiti
        if ut.config_data["anilist"]["favorite"] and status_list == 'COMPLETED':
            ut.console.clear()
            ut.console.print(f"Riproduco {anime.name} Ep. {anime.last_ep}", style="warning")
            favorite = ut.fzf(["sì","no"], "Mettere l'anime tra i preferiti? ") == "sì"

    Thread(target=anilist.update_anilist, args=(ut.config_data["anilist"]["token"],anime.anilist_id, episode.numeric(), status_list, rating, favorite)).start()

def open_videos(anime: Anime, episode: Anime.Episode, provider: providers.Provider) -> tuple[bool, int]:
    """
    Riproduce l'episodio dell'anime.
    Se un episodio è già stato scaricato, viene riprodotto dal file scaricato.
    Altrimenti, viene riprodotto in streaming.

    Args:
        anime (Anime): l'anime di cui riprodurre l'episodio.
        episode (Anime.Episode): l'episodio da riprodurre.
        provider (Provider): il provider da cui prendere il link dell'episodio.
    """

    #se il video è già stato scaricato lo riproduco invece di farlo in streaming
    path = f"{download.path(create=False)}/{anime.name}/{episode}.mp4"

    if Path(path).exists():
        ep_url = path if ut.os_name == "Android" else "file://" + path
    else:
        ep_url = provider.episode_link(anime, episode)

    ut.console.clear()
    ut.console.print(f"Riproduco {anime.name} Ep. {episode}", style="warning")
    return open_player(ep_url, str(episode), episode.progress)

def setup_config() -> None:
    """
    Crea un file di configurazione chiamato "config.toml"
    nella stessa directory dello script.
    Le informazioni riportate saranno scelte dall'utente.
    Sarà possibile scegliere il Player predefinito,
    se collegare il proprio profilo AniList e
    se inserire il path di syncplay.
    """
    ut.config_data.clear()

    #player predefinito
    ut.console.clear()
    ut.console.print("AW-CLI - CONFIGURAZIONE", style="warning")

    ut.config_data["player"]["type"] = ut.fzf(["vlc","mpv"], "Scegli il player predefinito: ")
    if ut.os_name != "Android":
        path = shutil.which(ut.config_data['player']['type'])
        if path is None:
            ut.console.print(f"Player {ut.config_data['player']['type']} non trovato!", style="error")
            ut.config_data["player"]["path"] = Prompt.ask(f"Inserisci il path di {ut.config_data['player']['type']} manualmente se è installato", console=ut.console)
        else:
            ut.config_data["player"]["path"] = path
        ut.console.clear()
        ut.console.print("AW-CLI - CONFIGURAZIONE", style="info")

    ut.config_data["general"]["specials"] = ut.fzf(["sì","no"], "Mostrare gli episodi speciali? ") == "sì"


    #provider preferito
    ut.config_data["provider"]["source"] = ut.fzf(["animeunity", "animeworld"], "Scegli il provider: ")

    #anilist
    if ut.fzf(["sì","no"], "Aggiornare automaticamente la watchlist con AniList? ") == "sì":
        link = "https://anilist.co/api/v2/oauth/authorize?client_id=11388&response_type=token"
        if ut.os_name == "Darwin":
            subprocess.run(f"open '{link}'", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.run(f"xdg-open '{link}'", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        #inserimento token
        ut.console.clear()
        ut.config_data["anilist"]["token"] = Prompt.ask(f"Inserire il token di AniList ({link})", console=ut.console)

        #prendo l'id dell'utente tramite query
        with ThreadPoolExecutor() as executor:
            ut.config_data["anilist"]["rating"], ut.config_data["anilist"]["favorite"], ut.config_data["anilist"]["drop"] = False, False, False
            future = executor.submit(anilist.get_user_id, ut.config_data["anilist"]["token"])
            ut.console.clear()
            ut.console.print("AW-CLI - CONFIGURAZIONE", style="info")
            if ut.fzf(["sì","no"], "Votare l'anime una volta completato? ") == "sì":
                ut.config_data["anilist"]["rating"] = True

            if ut.fzf(["sì","no"], "Chiedere se mettere l'anime tra i preferiti una volta completato? ") == "sì":
                ut.config_data["anilist"]["favorite"] = True

            if ut.fzf(["sì","no"], "Chiedere se droppare l'anime una volta rimosso dalla cronologia? ") == "sì":
                ut.config_data["anilist"]["drop"] = True

            ut.config_data["anilist"]["user_id"]  = future.result()

    #syncplay
    if ut.os_name != "Android":
        syncplay_path = shutil.which("syncplay")
        if syncplay_path is None:
            ut.console.print("Syncplay non trovato!", style="error")
            syncplay = Prompt.ask("Inserisci il path di Syncplay (premere INVIO se non lo si desidera utilizzare)", console=ut.console).replace("Program Files (x86)", "Progra~2")
            if syncplay != "":
                ut.config_data["syncplay"]["path"] = syncplay
        else:
            ut.config_data["syncplay"]["path"] = syncplay_path

    # style
    ut.config_data["style"] = ut.DEFAULT_STYLE

    #creo il file
    config = Path(__file__).parent / "config.toml"
    with open(config, 'w') as f:
        ut.toml.dump(ut.config_data, f)

def list_anime_names(animelist: list[Anime]) -> list[str]:
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
        colour = 2 #2 verde, 1 rosso
        if hist and a.curr_ep == a.last_ep and (not a.has_episode(a.curr_ep) or a.episode(a.curr_ep).is_completed()):
            colour = 1

        name = f"\033[0;3{colour}m{i + 1}  \033[0;37m"

        if hist:
            name += f"{a.name} [Ep {a.curr_ep}/{a.info['Episodi']}]"
        elif latest:
            name += f"{a.name} [Ep {a.curr_ep}]"
        else:
            name += f"{a.name}"
        names.append(name)

    return names

def remove_from_history(anime: Anime) -> None:
    """
    Rimuove l'anime selezionato dalla cronologia
    e stampa un menu di scelta per l'utente.

    Args:
        number (int): il numero dell'anime in lista da rimuovere.

    Returns:
        None.
    """

    if ut.fzf(["sì","no"], f"Si è sicuri di voler rimuovere {anime.name} dalla cronologia? ") == "no":
        return

    if "anilist" in ut.config_data and ut.config_data["anilist"]["drop"] and ut.fzf(["sì","no"], f"Droppare {anime.name} su AniList? ") == "sì":
        if anime.anilist_id == 0:
            ut.console.print("Impossibile droppare su AniList: id anime non trovato!", style="error")
            sleep(1)
        else:
            rating = anilist.get_anime_private_rating(ut.config_data["anilist"]["token"], ut.config_data["anilist"]["user_id"], anime.anilist_id)
            update_anilist(anime, anime.episode(anime.curr_ep), rating, drop=True)

    history.remove(anime)

    ut.console.clear()
    if ut.fzf(["esci","continua"]) == "esci":
        exit()

def main():
    global open_player
    global history

    #se il file di configurazione non esiste viene chiesto all'utente di fare il setup
    if args.start_config or not (Path(__file__).parent / "config.toml").exists():
        setup_config()

    ut.get_config()
    history = History.read(str(Path(__file__).parent))

    if offline:
        from .providers.local import LocalProvider
        provider = LocalProvider(download.path(), history.get())
    else:
        match ut.config_data["provider"]["source"]:
            case "animeunity":
                from .providers.animeunity import Animeunity
                provider = Animeunity()
            case _:
                from .providers.animeworld import Animeworld
                provider = Animeworld()

    if ut.config_data["player"]["type"] == "vlc":
        open_player = open_vlc
    if ut.os_name != "Android" and args.syncpl:
        open_player = open_syncplay

    reload = True
    animelist = []
    while True:
        if reload:
            if offline:
                animelist = provider.search("") # Uses offline provider
            elif hist:
                animelist = history.get()
            elif latest:
                animelist = provider.latest(args.latest)
            else:
                animelist = search_anime(provider)

            if not animelist:
                message = "Cronologia vuota!" if hist else "Nessun anime trovato!"
                ut.console.print(message, style="error")
                exit()

        if hist and args.history != 'r':
            history.reload(provider.latest())
            pass

        ut.console.clear()
        prompt = "Scegli un anime: " if args.history != 'r' else "Rimuovi un anime: "
        selected_anime = ut.fzf(list_anime_names(animelist), prompt)
        selected = int(selected_anime.split("  ")[0]) - 1
        anime = animelist[selected]

        if args.history == 'r':
            remove_from_history(anime)
            continue

        try:
            provider.info_anime(anime)
        except LookupError as error:
            ut.console.print(str(error), style="error")
            ut.console.print("Cercarlo manualmente", style="highlight")
            exit()

        if info:
            ut.console.clear()
            ut.console.print(anime)
            #stampo piccolo menu per scegliere se guardare l'anime o tornare indietro
            if ut.fzf(["indietro","guardare"]) == "indietro":
                continue

        if len(anime.episodes()) == 0:
            provider.episodes(anime)

        if len(anime.episodes()) == 0:
            ut.console.print("Eh, volevi! L'anime non è ancora stato rilasciato", style="error")
            sleep(1)
            reload = False
            continue

        if hist and anime.episode(anime.curr_ep).is_completed():
            if not anime.episode(anime.curr_ep).has_next():
                provider.episodes(anime)

            if not anime.episode(anime.curr_ep).has_next():
                ut.console.print(f"L'episodio {anime.episode(anime.curr_ep).numeric() + 1} di {anime.name} non è ancora stato rilasciato!", style="error")
                sleep(1)
                if len(animelist) == 1:
                    exit()
                reload = False
                continue
            episodes = [anime.episode(anime.curr_ep).next()]
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

            answer = ut.fzf(["esci","indietro","guarda"])
            if answer == "esci":
                exit()
            if answer == "indietro":
                continue

        while True:
            anilist_rating = None
            if not (offline or private) and "anilist" in ut.config_data:
                executor = ThreadPoolExecutor(max_workers=1)
                anilist_rating = executor.submit(anilist.get_anime_private_rating, ut.config_data["anilist"]["token"], ut.config_data["anilist"]["user_id"], anime.anilist_id)

            completed, progress = open_videos(anime, episode, provider)

            if not private:
                episode.set_progress(progress)
                if completed:
                    episode.mark_completed()
                    #update watchlist anilist se ho fatto l'accesso
                    if anilist_rating:
                        update_anilist(anime, episode, anilist_rating.result())

                anime.curr_ep = episode.num
                history.update(anime, episode)

            # menù che si visualizza dopo aver finito la riproduzione
            menu = ["esci", "indietro"]

            if anime.last_ep != '1':
                menu.append("seleziona")
            if episode.has_prev() or (not offline and episode.numeric() > 1):
                menu.append("antecedente")
            menu.append("riguarda")
            if episode.has_next() or (not offline and episode.num != anime.last_ep):
                menu.append("prossimo")

            menu_selection = ut.fzf(menu)

            if menu_selection == "prossimo":
                if not episode.has_next():
                    provider.episodes(anime)
                episode = episode.next()
            elif menu_selection == "antecedente":
                if not episode.has_prev():
                    provider.episodes(anime)
                episode = episode.prev()
            elif menu_selection == "seleziona":
                if not offline and len(anime.episodes()) == 1:
                    provider.episodes(anime)
                episode = select_episodes(anime)[0]
            elif menu_selection == "indietro":
                break
            elif menu_selection == "esci":
                exit()

        reload = True

history = History()
open_player = open_mpv
complete_limit = 90

if __name__ == "__main__":
    main()
