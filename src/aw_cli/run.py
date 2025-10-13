import os
import re
from signal import signal, SIGINT
from concurrent.futures import ThreadPoolExecutor
from threading import Thread
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
    lista,
    offline,
    privato,
    cronologia,
)

signal(SIGINT, lambda signum, frame: exit())

def fzf(elementi: list[str], prompt: str = "> ", multi: bool = False, cls: bool = False, esci: bool = True) -> str:
    """
    Avvia fzf con impostazioni predefinite.

    Args:
        elementi (list[str]): lista da passare ad fzf con gli elementi da selezionare.
        prompt (str, optional): il prompt che fzf deve stampare. Valore predefinito: "> ".
        multi (bool, optional): se True, permette la selezione multipla, con aggiunta di un costum bind crtl+a che
         permette di selezionare tutto. Valore predefinito: False.
        cls (bool, optional): se impostato a True, pulisce lo schermo prima di stampare il testo. Valore predefinito: False.
        esci (bool, optional): se True, esce dal programma se l'input dell'utente è vuoto. Valore predefinito: True.

    Returns:
        str: la scelta selezionata tramite fzf.
    """

    if cls:
        ut.my_print("", end="", cls=True)
    string = "\n".join(elementi)
    comando = f"""fzf --tac --height={len(elementi) + 2} --cycle --ansi --tiebreak=begin --prompt="{prompt}" """
    if multi:
        comando += "--multi --bind 'ctrl-a:toggle-all'"
    output = os.popen(f"""printf "{string}" | {comando}""").read().strip()

    if esci and output == "":
        exit()

    return output

def RicercaAnime(provider: providers.Provider) -> list[Anime]:
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

    ut.my_print("", end="", cls=True)
    return ut.my_input("Cerca un anime", check_search,"La ricerca non ha prodotto risultati", cls = True)

def scegliEpisodi(anime) -> list[Anime.Episode]:
    """
    Fa scegliere all'utente gli episodi dell'anime da guardare.

    Se l'anime ha solo un episodio, questo verrà riprodotto automaticamente.
    In caso contrario, l'utente può scegliere un episodio.

    Returns:
        str: il numero dell'episodio da riprodurre.
    """


    ut.my_print(anime.name, cls=True)
    #se contiene solo 1 ep sarà riprodotto automaticamente
    if len(anime.episodes()) == 1:
        return anime._episodes

    res = fzf(list(reversed(anime.episodes())), "Scegli un episodio: ", multi=downl).split("\n")
    return [anime.episode(num) for num in res]

def openSyncplay(url_ep: str, nome_video: str, progress: int) -> tuple[bool, int]:
    """
    Avvia Syncplay.

    Args:
        url_ep (str): l'URL dell'episodio da riprodurre.
        nome_video (str): il nome dell'episodio.
        progress (int): il progresso dell'episodio.

    Returns:
        bool: True se l'episodio è stato riprodotto completamente, altrimenti False.
        int: il progresso dell'episodio.
    """

    if "syncplay" not in ut.configData:
        ut.my_print("Aggiornare il path di syncplay nella configurazione tramite: aw-cli -a", color="rosso")
        exit()


    args = f'''--force-media-title="{nome_video}" --start="{progress}" --fullscreen --keep-open'''
    if ut.configData["player"]["type"] == "vlc":
        args = f'''--meta-title "{nome_video}" --start-time="{progress}" --fullscreen'''

    try :
        out = os.popen(f'''{ut.configData["syncplay"]["path"]} -d --language it "{url_ep}" -- {args} 2>&1''').read()
    except UnicodeDecodeError:
        out = ""

    duration_match = re.findall(r'duration(?:-change)?"?: (\d+)\.?[\d]*', out)
    progress_match = re.findall(r'pos(?:ition"?)?:? (\d+).?\d+', out)
    if not duration_match:
        ut.my_print("Errore, impossibile leggere l'output di Syncplay!", color="rosso")
        return False, 0

    duration = max(map(int, duration_match))
    progress_match = list(filter(lambda x: x>0, map(int, progress_match)))
    progress = progress_match[-1] if progress_match else 0

    return progress*100// duration >= completeLimit if duration > 0 else False, progress

def openMPV(url_ep: str, nome_video: str, progress: int) -> tuple[bool, int]:
    """
    Apre MPV per riprodurre il video.

    Args:
        url_server (str): il link del video o il percorso del file.
        nome_video (str): il nome del video.
        progress (int): il progresso dell'episodio.

    Returns:
        bool: True se l'episodio è stato riprodotto completamente, altrimenti False.
        int: il progresso dell'episodio.
    """


    if (ut.nome_os == "Android"):
        os.system(f'''am start --user 0 -a android.intent.action.VIEW -d "{url_ep}" -n is.xyz.mpv/.MPVActivity > /dev/null 2>&1''')
        return True, 0

    out = os.popen(f'''{ut.configData["player"]["path"]} "{url_ep}" --force-media-title="{nome_video}" --start="{progress}" --fullscreen --keep-open 2>&1''')

    res = re.findall(r'(\d+):(\d+):(\d+) / [\d:]+ \((\d+)%\)', out.read())[-1]
    progress = (int(res[0]) * 3600) + (int(res[1]) * 60) + int(res[2])

    return int(res[3]) >= completeLimit, progress

def openVLC(url_ep: str, nome_video: str, progress: int) -> tuple[bool, int]:
    """
    Apre VLC per riprodurre il video.

    Args:
        url_server (str): il link del video o il percorso del file.
        nome_video (str): il nome del video.
        progress (int): il progresso dell'episodio.

    Returns:
        bool: True se l'episodio è stato riprodotto completamente, altrimenti False.
        int: il progresso dell'episodio.
    """

    if ut.nome_os == "Android":
        os.system(f'''am start --user 0 -a android.intent.action.VIEW -d "{url_ep}" -n org.videolan.vlc/.StartActivity -e "title" "{nome_video}" > /dev/null 2>&1''')
        return True, 0

    os.system(f'''{ut.configData["player"]["path"]} "{url_ep}" --meta-title "{nome_video}" --start-time="{progress}" --fullscreen > /dev/null 2>&1''')

    # se il file di configurazione di VLC esiste, prendo la posizione dell'ultimo episodio riprodotto
    progress = 0
    vlc_config_path = os.path.expanduser("~/.config/vlc/vlc-qt-interface.conf") # Linux
    if os.path.exists(vlc_config_path):
        with open(vlc_config_path, "r") as file:
            config = [line.strip() for line in file.readlines()]
            index = config.index("[RecentsMRL]")
            urls = config[index + 1].split("=")[1].split(", ")
            positions = config[index + 2].split("=")[1].split(", ")
        progress = int(positions[urls.index(url_ep)]) // 1000 if url_ep in urls else 0

    # Non informazioni sulla durata: suppongo che sia completato
    return True, progress

def update_anilist(anime: Anime, episode: Anime.Episode, anilist_rating: float|None, drop: bool = False):
    """
    Procede ad aggiornare l'anime su AniList.
    Se l'episodio riprodotto è l'ultimo e
    l'utente ha scelto di votare gli anime,
    verrà chiesto il voto da dare.

    Args:
        ep (Anime.Episode): l'episodio da aggiornare.
        anilist_rating (float): il voto che l'utente ha assegnato all'anime.
        drop (bool, optional): True se l'utente decide di droppare l'anime, altrimenti False.
    """

    if anime.id_anilist == 0:
        ut.my_print("Impossibile aggiornare AniList: id anime non trovato!", color="rosso")
        return

    rating = 0
    favorite = False
    status_list = 'CURRENT' if not drop else 'DROPPED'
    #se ho finito di vedere l'anime o lo stato è dropped
    if (episode.numeric() == int(anime.last_ep) and anime.status == AnimeStatus.FINISHED) or status_list == 'DROPPED':
        if status_list == 'CURRENT':
            status_list = 'COMPLETED'

        #chiedo di votare
        if ut.configData["anilist"]["rating"]:
            rating = ut.my_input(
                "Inserisci un voto per l'anime" + (f" (voto corrente: {anilist_rating})" if anilist_rating else ""),
                lambda n: float(n) if n.replace('.', '', 1).isdigit() else None
            )

        #chiedo di mettere tra i preferiti
        if ut.configData["anilist"]["favorite"] and status_list == 'COMPLETED':
            ut.my_print(f"Riproduco {anime.name} Ep. {anime.last_ep}", color="giallo", cls=True)
            favorite = fzf(["sì","no"], "Mettere l'anime tra i preferiti? ") == "sì"

    Thread(target=anilist.updateAnilist, args=(ut.configData["anilist"]["token"],anime.id_anilist, episode.numeric(), status_list, rating, favorite)).start()

def openVideos(anime: Anime, episode: Anime.Episode, provider: providers.Provider) -> tuple[bool, int]:
    """
    Riproduce l'episodio dell'anime.
    Se un episodio è già stato scaricato, viene riprodotto dal file scaricato.
    Altrimenti, viene riprodotto in streaming.

    Args:
        episode (Anime.Episode): l'episodio da riprodurre.
    """

    #se il video è già stato scaricato lo riproduco invece di farlo in streaming
    path = f"{download.path(create=False)}/{anime.name}/{episode}.mp4"

    if os.path.exists(path):
        url_ep = path if ut.nome_os == "Android" else "file://" + path
    else:
        url_ep = provider.episode_link(anime, episode)

    ut.my_print(f"Riproduco {episode}...", color="giallo", cls=True)
    return openPlayer(url_ep, str(episode), episode.progress)

def setupConfig() -> None:
    """
    Crea un file di configurazione chiamato "config.toml"
    nella stessa directory dello script.
    Le informazioni riportate saranno scelte dall'utente.
    Sarà possibile scegliere il Player predefinito,
    se collegare il proprio profilo AniList e
    se inserire il path di syncplay.
    """
    ut.configData.clear()

    #player predefinito
    ut.my_print("", end="", cls=True)
    ut.my_print("AW-CLI - CONFIGURAZIONE", color="giallo")

    ut.configData["player"]["type"] = fzf(["vlc","mpv"], "Scegli il player predefinito: ")
    if ut.nome_os != "Android":
        res = os.popen(f"whereis -b {ut.configData['player']['type']} 2>&1").read().removeprefix(f"{ut.configData['player']['type']}:").strip().split()
        if len(res) == 0:
            ut.my_print(f"Player {ut.configData['player']['type']} non trovato!", color="rosso")
            ut.configData["player"]["path"] = ut.my_input(f"Inserisci il path di {ut.configData['player']['type']} manualmente se è installato")
        else:
            ut.configData["player"]["path"] = res[0]
        ut.my_print("AW-CLI - CONFIGURAZIONE", color="giallo", cls=True)

    ut.configData["general"]["specials"] = fzf(["sì","no"], "Mostrare gli episodi speciali? ") == "sì"


    #provider preferito
    ut.configData["provider"]["source"] = fzf(["animeunity", "animeworld"], "Scegli il provider: ")

    #anilist
    if fzf(["sì","no"], "Aggiornare automaticamente la watchlist con AniList? ") == "sì":
        link = "https://anilist.co/api/v2/oauth/authorize?client_id=11388&response_type=token"
        if ut.nome_os == "Darwin":
            os.system(f"open '{link}' > /dev/null 2>&1")
        else:
            os.system(f"xdg-open '{link}' > /dev/null 2>&1")


        #inserimento token
        ut.configData["anilist"]["token"] = ut.my_input(f"Inserire il token di AniList ({link})", cls=True)

        #prendo l'id dell'utente tramite query
        with ThreadPoolExecutor() as executor:
            ut.configData["anilist"]["rating"], ut.configData["anilist"]["favorite"], ut.configData["anilist"]["drop"] = False, False, False
            future = executor.submit(anilist.getAnilistUserId, ut.configData["anilist"]["token"])
            ut.my_print("AW-CLI - CONFIGURAZIONE", color="giallo", cls=True)
            if fzf(["sì","no"], "Votare l'anime una volta completato? ") == "sì":
                ut.configData["anilist"]["rating"] = True

            if fzf(["sì","no"], "Chiedere se mettere l'anime tra i preferiti una volta completato? ") == "sì":
                ut.configData["anilist"]["favorite"] = True

            if fzf(["sì","no"], "Chiedere se droppare l'anime una volta rimosso dalla cronologia? ") == "sì":
                ut.configData["anilist"]["drop"] = True

            ut.configData["anilist"]["user_id"]  = future.result()

    #syncplay
    if ut.nome_os != "Android":
        res = os.popen("whereis -b syncplay 2>&1").read().removeprefix("syncplay:").strip().split()
        if len(res) == 0:
            ut.my_print("Syncplay non trovato!", color="rosso")
            syncplay = ut.my_input("Inserisci il path di Syncplay (premere INVIO se non lo si desidera utilizzare)").replace("Program Files (x86)", "Progra~2")
            if syncplay != "":
                ut.configData["syncplay"]["path"] = syncplay
        else:
            ut.configData["syncplay"]["path"] = res[0]

    #creo il file
    config = f"{os.path.dirname(__file__)}/config.toml"
    with open(config, 'w') as f:
        ut.toml.dump(ut.configData, f)

def listAnimeNames(animelist: list[Anime]) -> list[str]:
    """
    Genera una lista di stringhe formattate con i
    nomi degli anime presenti nella lista desiderata.

    Args:
        animelist (list[Anime]): Una lista Anime.

    Return:
        str: lista di stringhe formattate.
    """

    nomi = []
    for i, a in reversed(list(enumerate(animelist))):
        colore = 2 #2 verde, 1 rosso
        if cronologia and a.curr_ep == a.last_ep and (not a.has_episode(a.curr_ep) or a.episode(a.curr_ep).is_completed()):
            colore = 1

        nome = f"\033[0;3{colore}m{i + 1}  \033[0;37m"

        if cronologia:
            nome += f"{a.name} [Ep {a.curr_ep}/{a.info['Episodi']}]"
        elif lista:
            nome += f"{a.name} [Ep {a.curr_ep}]"
        else:
            nome += f"{a.name}"
        nomi.append(nome)

    return nomi

def removeFromCrono(anime: Anime) -> None:
    """
    Rimuove l'anime selezionato dalla cronologia
    e stampa un menu di scelta per l'utente.

    Args:
        number (int): il numero dell'anime in lista da rimuovere.

    Return:
        None.
    """

    if fzf(["sì","no"], f"Si è sicuri di voler rimuovere {anime.name} dalla cronologia? ") == "no":
        return

    if "anilist" in ut.configData and ut.configData["anilist"]["drop"] and fzf(["sì","no"], f"Droppare {anime.name} su AniList? ") == "sì":
        if anime.id_anilist == 0:
            ut.my_print("Impossibile droppare su AniList: id anime non trovato!", color="rosso")
            ut.sleep(1)
        else:
            rating = anilist.getAnimePrivateRating(ut.configData["anilist"]["token"], ut.configData["anilist"]["user_id"], anime.id_anilist)
            update_anilist(anime, anime.episode(anime.curr_ep), rating, drop=True)

    history.remove(anime)

    if fzf(["esci","continua"], cls=True) == "esci":
        exit()

def main():
    global openPlayer
    global history

    #se il file di configurazione non esiste viene chiesto all'utente di fare il setup
    if args.avvia_config or not os.path.exists(f"{os.path.dirname(__file__)}/config.toml"):
        setupConfig()

    ut.getConfig()
    history = History.read(os.path.dirname(__file__))

    if offline:
        from .providers.local import LocalProvider
        provider = LocalProvider(download.path(), history.get())
    else:
        match ut.configData["provider"]["source"]:
            case "animeunity":
                from .providers.animeunity import Animeunity
                provider = Animeunity()
            case _:
                from .providers.animeworld import Animeworld
                provider = Animeworld()

    if ut.configData["player"]["type"] == "vlc":
        openPlayer = openVLC
    if ut.nome_os != "Android" and args.syncpl:
        openPlayer = openSyncplay

    reload = True
    animelist = []
    while True:
        if reload:
            if offline:
                animelist = provider.search("") # Uses offline provider
            elif cronologia:
                animelist = history.get()
            elif lista:
                animelist = provider.latest(args.lista)
            else:
                animelist = RicercaAnime(provider)

            if not animelist:
                message = "Cronologia vuota!" if cronologia else "Nessun anime trovato!"
                ut.my_print(message, color="rosso")
                exit()

        ut.my_print("", end="", cls=True)
        esci = True
        if cronologia and args.cronologia != 'r':
            history.reload(provider.latest())
            pass

        prompt = "Scegli un anime: " if args.cronologia != 'r' else "Rimuovi un anime: "
        scelta_anime = fzf(listAnimeNames(animelist), prompt, esci=esci)

        scelta = int(scelta_anime.split("  ")[0]) - 1
        anime = animelist[scelta]

        if args.cronologia == 'r':
            removeFromCrono(anime)
            continue

        try:
            provider.info_anime(anime)
        except LookupError as error:
            ut.my_print(str(error), color="rosso")
            ut.my_print("Cercarlo manualmente", color="magenta")
            exit()

        if info:
            anime.print_info()
            #stampo piccolo menu per scegliere se guardare l'anime o tornare indietro
            if fzf(["indietro","guardare"]) == "indietro":
                continue

        if len(anime.episodes()) == 0:
            provider.episodes(anime)

        if len(anime.episodes()) == 0:
            ut.my_print("Eh, volevi! L'anime non è ancora stato rilasciato", color="rosso")
            ut.sleep(1)
            reload = False
            continue

        if cronologia and anime.episode(anime.curr_ep).is_completed():
            if not anime.episode(anime.curr_ep).has_next():
                provider.episodes(anime)

            if not anime.episode(anime.curr_ep).has_next():
                ut.my_print(f"L'episodio {anime.episode(anime.curr_ep).numeric() + 1} di {anime.name} non è ancora stato rilasciato!", color='rosso')
                ut.sleep(1)
                if len(animelist) == 1:
                    exit()
                reload = False
                continue
            listaEpisodi = [anime.episode(anime.curr_ep).next()]
        elif lista or cronologia:
            listaEpisodi = [anime.episode(anime.curr_ep)]
        else:
            listaEpisodi = scegliEpisodi(anime)

        episode = listaEpisodi[0]

        if downl:
            download.episodes(anime, listaEpisodi, provider)

            anime.curr_ep = episode.num
            if not any(anime == a for a in history.get()):
                history.update(anime, episode)

            risp = fzf(["esci","indietro","guarda"])
            if risp == "esci":
                exit()
            if risp == "indietro":
                continue

        while True:
            voto_anilist = None
            if not (offline or privato) and "anilist" in ut.configData:
                executor = ThreadPoolExecutor(max_workers=1)
                voto_anilist = executor.submit(anilist.getAnimePrivateRating, ut.configData["anilist"]["token"], ut.configData["anilist"]["user_id"], anime.id_anilist)

            completed, progress = openVideos(anime, episode, provider)

            if not privato:
                episode.set_progress(progress)
                if completed:
                    episode.mark_completed()
                    #update watchlist anilist se ho fatto l'accesso
                    if voto_anilist:
                        update_anilist(anime, episode, voto_anilist.result())

                anime.curr_ep = episode.num
                history.update(anime, episode)

            # menù che si visualizza dopo aver finito la riproduzione
            lista_menu = ["esci", "indietro"]

            check = lambda: False
            get = lambda: None
            if anime.last_ep != '1':
                lista_menu.append("seleziona")
                check = lambda: offline or len(anime.episodes()) != 1
                get = lambda: scegliEpisodi(anime)[0]
            if episode.has_prev() or (not offline and episode.numeric() > 1):
                lista_menu.append("antecedente")
                check, get = episode.has_prev, episode.prev
            lista_menu.append("riguarda")
            if episode.has_next() or (not offline and episode.num != anime.last_ep):
                lista_menu.append("prossimo")
                check, get = episode.has_next, episode.next

            scelta_menu = fzf(lista_menu)

            if scelta_menu in ["prossimo", "antecedente", "seleziona"]:
                if not check():
                    provider.episodes(anime)
                episode = get()
            elif scelta_menu == "indietro":
                break
            elif scelta_menu == "esci":
                exit()
        reload = True

history = History()
openPlayer = openMPV
completeLimit = 90

if __name__ == "__main__":
    main()
