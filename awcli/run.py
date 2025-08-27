import os
import re
import csv
from signal import signal, SIGINT
from concurrent.futures import ThreadPoolExecutor
from pySmartDL import SmartDL
from pathlib import Path
from threading import Thread
from awcli import anilist, utilities as ut
from awcli.anime import Anime, Episode
from awcli.arg_parser import *

def safeExit():
    with open(f"{os.path.dirname(__file__)}/aw-cronologia.csv", 'w', newline='', encoding='utf-8') as file:
        csv.writer(file).writerows(log)
    exit()

signal(SIGINT, lambda signum, frame: safeExit())

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
        safeExit()

    return output

def RicercaAnime() -> list[Anime]:
    """
    Dato in input un nome di un anime inserito dall'utente, restituisce una lista con gli URL degli anime
    relativi alla ricerca.

    Returns:
        list[Anime]: la lista con gli URL degli anime trovati
    """

    def check_search(s: str):
        if s == "exit":
            safeExit() 
        result = provider.search(s)
        if len(result) != 0:
            return result

    ut.my_print("", end="", cls=True)
    return ut.my_input("Cerca un anime", check_search,"La ricerca non ha prodotto risultati", cls = True)

def animeScaricati(path: str) -> list[Anime]:
    """
    Prende i nomi degli anime scaricati nella cartella Video/Anime.

    Args:
        path (str): il path relativo alla cartella Video/Anime

    Returns:
        list[Anime]: la lista degli anime trovati
    """
    nomi = os.listdir(path)

    if len(nomi) == 0:
        ut.my_print("Nessun anime scaricato", color='rosso')
        safeExit()

    animes = list[Anime]()
    for name in nomi:
        animes.append(Anime(name, f"{path}/{name}"))
    return animes

def scegliEpisodi() -> list[Episode]:
    """
    Fa scegliere all'utente gli episodi dell'anime da guardare.

    Se l'anime ha solo un episodio, questo verrà riprodotto automaticamente.
    In caso contrario, l'utente può scegliere un episodio.

    Returns:
        str: il numero dell'episodio da riprodurre.
    """

    
    ut.my_print(anime.name, cls=True)
    #se contiene solo 1 ep sarà riprodotto automaticamente
    if anime.last_ep == 1:
        return anime._episodes

    res = fzf(list(reversed(anime.episodes())), "Scegli un episodio: ", multi=downl).split("\n")
    return list(map(lambda num: anime.episode(num), sorted(res)))

def downloadPath(create: bool = True) -> str:
    """
    Restituisce il percorso di download dell'anime, a seconda del sistema operativo in uso.
    Se create è True (valore predefinito) e il percorso non esiste, viene creato.

    Args:
        create (bool, optional): se impostato a True, crea il percorso se non esiste. Valore predefinito: True.

    Returns:
        str: il percorso di download dell'anime.
    """

    if (ut.nome_os == "Android"):
        path = f"/sdcard/Movies/Anime"
    else:
        path = f"{Path.home()}/Videos/Anime"
    if create and not os.path.exists(path):
        os.makedirs(path)
    return path

def scaricaEpisodio(ep: Episode, path: str):
    """
    Scarica l'episodio dell'anime e lo salva nella cartella specificata.
    Se l'episodio è già presente nella cartella, non viene riscaricato.

    Args:
        ep (Episode): L'episodio da scaricare.
        path (str): il percorso dove salvare l'episodio.
    """
    # se l'episodio non è ancora stato scaricato lo scarico, altrimenti skippo
    ut.my_print(ep, color="blu", end=":\n")
    if not os.path.exists(f"{path}/{ep}.mp4"):
        SDL = SmartDL(provider.episode_link(anime, ep), f"{path}/{ep}.mp4")
        SDL.start()
    else:
        ut.my_print("già scaricato, skippo...", color="giallo")

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
        safeExit()
    
    
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
    vlc_config_path = os.path.expanduser("~/.config/vlc/vlc-qt-interface.conf")
    if os.path.exists(vlc_config_path):
        with open(vlc_config_path, "r") as file:
            config = [line.strip() for line in file.readlines()]
            index = config.index("[RecentsMRL]")
            urls = config[index + 1].split("=")[1].split(", ")
            positions = config[index + 2].split("=")[1].split(", ")
        progress = int(positions[urls.index(url_ep)]) // 1000 if url_ep in urls else 0
    
    tmp = anime.info["Durata"].split()
    # se non ho informazioni sul progresso, suppongo che sia completato
    if progress == 0:
        return True, 0
    
    # se non ho informazioni sulla durata dell'episodio, suppongo non sia completato
    if tmp[0] == "??":
        return False, progress

    # stimo la durata dell'episodio in secondi    
    if tmp[0].endswith("h"):
        duration = int(tmp[0][:-1]) * 3600 + int(tmp[2]) * 60
    else:
        duration = int(tmp[0]) * 60
        
    # se il progresso è maggiore della durata dell'episodio la sitma è errata
    if progress > duration:
        return False, progress
    
    return progress*100//duration >= completeLimit, progress

def addToCronologia(ep: int, progress: int):
    """
    Aggiorna la cronologia con le informazioni esseziali relative all'episodio visualizzato.
    Le informazioni sono:
    - nome dell'anime
    - episodio visualizzato
    - URL dell'anime
    - numero totale di episodi
    - stato dell'anime
    - ultimo episodio disponibile
    - id dell'anime su AniList
    - progresso dell'episodio in secondi

    Args:
        ep (int): il numero dell'episodio visualizzato.
    """
    #rimuovo l'anime dalla cronologia se è già presente
    for i, riga in enumerate(log):
        if riga[6] == anime.id_anilist if anime.id_anilist else riga[0] == anime.name:
            log.pop(i)

    # se è stato completato l'ultimo episodio, non lo aggiungo alla cronologia 
    if ep == anime.last_ep and progress == 0 and anime.info["Stato"] == "1":
        return
    #aggiungo l'anime alla cronologia con i nuovi dati  
    new = [anime.name, ep, anime.url, anime.info["Episodi"], anime.info["Stato"], anime.last_ep, anime.id_anilist, progress]

    if ep == anime.last_ep and progress == 0:
        log.append(new)
    else:
        log.insert(0, new)

def updateAnilist(ep: int, voto_anilist: float, drop: bool = False):
    """
    Procede ad aggiornare l'anime su AniList.
    Se l'episodio riprodotto è l'ultimo e
    l'utente ha scelto di votare gli anime,
    verrà chiesto il voto da dare.

    Args:
        ep (int): il numero dell'episodio visualizzato.
        drop (bool, optional): True se l'utente decide di droppare l'anime, altrimenti False.
    """
    
    if anime.id_anilist == 0:
        ut.my_print("Impossibile aggiornare AniList: id anime non trovato!", color="rosso")
        return
    
    voto = 0
    preferiti = False
    status_list = 'CURRENT' if not drop else 'DROPPED'

    #se ho finito di vedere l'anime o lo stato è dropped    
    if (ep == anime.last_ep and anime.info["Stato"] == "1") or status_list == 'DROPPED':
        if status_list == 'CURRENT':
            status_list = 'COMPLETED'
    
        #chiedo di votare
        if ut.configData["anilist"]["rating"]:
            is_number = lambda n: float(n) if n.replace('.', '', 1).isdigit() else None
            voto = ut.my_input("Inserisci un voto per l'anime" + (f" (voto corrente: {voto_anilist})" if voto_anilist else ""), is_number)
    
        #chiedo di mettere tra i preferiti
        if ut.configData["anilist"]["favorite"] and status_list == 'COMPLETED':
            ut.my_print(f"Riproduco {anime.name} Ep. {anime.last_ep}", color="giallo", cls=True)
            preferiti = fzf(["sì","no"], "Mettere l'anime tra i preferiti? ") == "sì"
    
    Thread(target=anilist.updateAnilist, args=(ut.configData["anilist"]["token"],anime.id_anilist, ep, status_list, voto, preferiti)).start()

def openVideos(episodio: Episode):
    """
    Riproduce l'episodio dell'anime.
    Se un episodio è già stato scaricato, viene riprodotto dal file scaricato.
    Altrimenti, viene riprodotto in streaming.

    Args:
        ep (Episode): l'episodio da riprodurre.
    """

    #se il video è già stato scaricato lo riproduco invece di farlo in streaming
    path = f"{downloadPath(create=False)}/{anime.name}/{episodio}.mp4"

    if os.path.exists(path):
        url_ep = "file://" + path if ut.nome_os == "Android" else path
    elif offline:
        ut.my_print(f"Episodio {episodio} non scaricato, skippo...", color='giallo')
        return
    else:
        url_ep = provider.episode_link(anime, episodio)

    ut.my_print(f"Riproduco {episodio}...", color="giallo", cls=True)
    return openPlayer(url_ep, str(episodio), anime.progress.get(episodio.num, 0))

      

def getCronologia() -> list[Anime]:
    """
    Prende i dati dalla cronologia.

    Returns:
        list[Anime]: la lista degli anime trovati 

    """
    animes = []

    for riga in log:
        if len(riga) < 4:
            riga.append("??")
        if len(riga) < 5:
            riga.append(0)
        if len(riga) < 6:
            riga.append(riga[1])    
        if len(riga) < 7:
            riga.append(0)
        if len(riga) < 8:
            riga.append(0)
        anime = Anime(name=riga[0], url=riga[2], curr_ep=riga[1], last_ep=riga[5])
        anime.progress[anime.curr_ep] = int(riga[7])
        anime._set_info(riga[6], {"Episodi": riga[3], "Stato": riga[4]})
        animes.append(anime)

    #se il file esiste ma non contiene dati stampo un messaggio di errore
    if len(animes) == 0:
        ut.my_print("Cronologia inesistente!", color='rosso')
        safeExit()
    return animes

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
        res = os.popen(f"whereis -b {ut.configData["player"]["type"]} 2>&1").read().removeprefix(f"{ut.configData["player"]["type"]}:").strip().split()
        if len(res) == 0:
            ut.my_print(f"Player {ut.configData["player"]["type"]} non trovato!", color="rosso")
            ut.configData["player"]["path"] = ut.my_input(f"Inserisci il path di {ut.configData["player"]["type"]} manualmente se è installato")
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
        res = os.popen(f"whereis -b syncplay 2>&1").read().removeprefix(f"syncplay:").strip().split()
        if len(res) == 0:
            ut.my_print("Syncplay non trovato!", color="rosso")
            syncplay = ut.my_input(f"Inserisci il path di Syncplay (premere INVIO se non lo si desidera utilizzare)").replace("Program Files (x86)", "Progra~2")
            if syncplay != "": ut.configData["syncplay"]["path"] = syncplay
        else:
            ut.configData["syncplay"]["path"] = res[0]

    #creo il file
    config = f"{os.path.dirname(__file__)}/config.toml"
    with open(config, 'w') as f:
        ut.toml.dump(ut.configData, f)

def isGreen(anime: Anime) -> bool:
    """
    Controlla se ci sono episodi disponibili per l'anime.
    """
    return anime.info["Stato"] == "1" or anime.curr_ep != anime.last_ep or anime.progress[anime.curr_ep] != 0

def reloadCrono(cronologia: list[Anime]):
    """
    Aggiorna la cronologia degli anime con le ultime uscite disponibili e la ristampa.

    Questa funzione esamina ciascun anime nella lista `animelist` e verifica se sono disponibili nuove uscite.
    Se trova nuove uscite per un anime, ne aggiorna lo stato.

    Args:
        cronologia (list[Anime]): Una lista Anime in cronologia.

    """
    global scelta_anime
    global notSelected

    if "0" not in [anime.info["Stato"] for anime in cronologia]:
        return
    
    ut.my_print("Ricerco le nuove uscite...", color="giallo")
    ultime_uscite = provider.latest()
    ut.my_print(end="", cls=True)
    testo = []

    for i, a in reversed(list(enumerate(cronologia))):
        colore = 1 #rosso
        if isGreen(a):
            colore = 2
        else:
            for anime_latest in ultime_uscite:
                if a.name == anime_latest.name and a.curr_ep < anime_latest.last_ep:
                    log[i][5] = anime_latest.last_ep
                    colore = 2
                    break
        testo.append(f"\033[0;3{colore}m{i + 1}  \033[0;37m{a.name} [Ep {a.curr_ep}/{a.info['Episodi']}]")
    
    if notSelected:
        pid = os.popen("pgrep fzf").read().strip().split("\n")
        os.system(f"kill {pid[-1]}")
        scelta_anime = fzf(testo, "Scegli un anime: ")

def listAnimeNames(animelist: list[Anime]) -> list[str]: 
    """
    Genera una lista di stringhe formattate con i 
    nomi degli anime presenti nella lista desiderata.

    Args:
        animelist (list[Anime]): Una lista Anime.    

    Return: 
        str: lista di stringhe formattate.
    """

    colore = 2 #2 verde, 1 rosso
    nomi = []

    for i, a in reversed(list(enumerate(animelist))):
        if cronologia and not isGreen(a):
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

def removeFromCrono(number: int):
    """
    Rimuove l'anime selezionato dalla cronologia
    e stampa un menu di scelta per l'utente.

    Args:
        number (int): il numero dell'anime in lista da rimuovere.

    Return:
        None.
    """

    global log

    if fzf(["sì","no"], f"Si è sicuri di voler rimuovere {anime.name} dalla cronologia? ") == "no":
        return

    if "anilist" in ut.configData and ut.configData["anilist"]["drop"] and fzf(["sì","no"], f"Droppare {anime.name} su AniList? ") == "sì":
        if anime.id_anilist == 0:
            ut.my_print("Impossibile droppare su AniList: id anime non trovato!", color="rosso")
            ut.sleep(1)
        else:
            rating = anilist.getAnimePrivateRating(ut.configData["anilist"]["token"], ut.configData["anilist"]["user_id"], anime.id_anilist)
            updateAnilist(anime.curr_ep, rating, drop=True)

    log.pop(number)

    if fzf(["esci","continua"], cls=True) == "esci":
        safeExit()

def updateScript():
    """
    Aggiorna di default il programma in base 
    all'ultima versione stabile.
    Se viene specificato il branch,
    verrà installato que#se il file di configurazione non esiste viene chiesto all'utente di fare il setup
    if args.avvia_config or not os.path.exists(f"{os.path.dirname(__file__)}/config.toml"):
        setupConfig()st'ultimo.
    """

    if args.update == None:
        comando = "echo y | python3 -m pip uninstall aw-cli > /dev/null 2>&1 && python3 -m pip install aw-cli > /dev/null 2>&1"
    else: 
        comando = f"echo y | python3 -m pip uninstall aw-cli > /dev/null 2>&1 && python3 -m pip install git+https://github.com/fexh10/aw-cli.git@{args.update} > /dev/null 2>&1"

    os.system(comando)
    
    ut.my_print("aw-cli aggiornato con successo!", color="bianco")
    exit()

def main():
    global log
    global anime
    global provider
    global openPlayer
    global scelta_anime
    global notSelected

    if update:
        updateScript()

    try:
        with open(f"{os.path.dirname(__file__)}/aw-cronologia.csv", encoding='utf-8') as file:
            log = [riga for riga in csv.reader(file)]
    except FileNotFoundError:
        pass
    
    #se il file di configurazione non esiste viene chiesto all'utente di fare il setup
    if args.avvia_config or not os.path.exists(f"{os.path.dirname(__file__)}/config.toml"):
        setupConfig()

    ut.getConfig()

    match ut.configData["provider"]["source"]:
        case "animeunity":
            from awcli.providers.animeunity import Animeunity
            provider = Animeunity()
        case _:
            from awcli.providers.animeworld import Animeworld
            provider = Animeworld()

    openPlayer = openMPV if ut.configData["player"]["type"] == "mpv" else openVLC

    if ut.nome_os != "Android" and args.syncpl:
        openPlayer = openSyncplay

    reload = True
    while True:
        if reload:
            if cronologia:
                animelist = getCronologia()
            elif lista:
                animelist = provider.latest(args.lista)
            else:
                animelist = RicercaAnime()
            if offline:
                animelist = [anime for anime in animelist if anime.name in [a.name for a in animeScaricati(downloadPath())]]

        ut.my_print("", end="", cls=True)
        esci = True
        if cronologia and args.cronologia != 'r':
            notSelected = True 
            thread = Thread(target=reloadCrono, args=[animelist])    
            thread.start()
            esci = False

        prompt = "Scegli un anime: " if args.cronologia != 'r' else "Rimuovi un anime: "
        scelta_anime = fzf(listAnimeNames(animelist), prompt, esci=esci)
        notSelected = False
        if cronologia and args.cronologia != 'r' and thread.is_alive:
                #controllo se l'utente ha selezionato un anime oppure se c'è stata la relaodCrono
                if scelta_anime == "":
                    thread.join()
                    if scelta_anime == "":
                        safeExit()                        

        scelta = int(scelta_anime.split("  ")[0]) - 1
        anime = animelist[scelta]

        if args.cronologia == 'r':
            removeFromCrono(scelta)
            continue

        if info:
            provider.info_anime(anime)
            anime.print_info()
            #stampo piccolo menu per scegliere se guardare l'anime o tornare indietro
            if fzf(["indietro","guardare"]) == "indietro":
                continue

        if offline:
            ut.downloaded_episodes(anime,f"{downloadPath()}/{anime.name}")
        elif len(anime.episodes()) < 1:
            provider.episodes(anime)

        if anime.last_ep == '0':
            ut.my_print("Eh, volevi! L'anime non è ancora stato rilasciato", color="rosso")
            ut.sleep(1)
            reload = False
            continue      

        
        if cronologia and anime.progress[anime.curr_ep] == 0:
            episode = anime.episode(anime.curr_ep)
            next = episode.next()
            if next is None:
                ut.my_print(f"L'episodio {episode.numeric() + 1} di {anime.name} non è ancora stato rilasciato!", color='rosso')
                ut.sleep(1)
                if len(animelist) == 1:
                    safeExit()
                reload = False
                continue
            listaEpisodi = [next]
        elif lista or cronologia:
            listaEpisodi = [anime.episode(anime.curr_ep)]
        else:
            listaEpisodi = scegliEpisodi()
            
        episode = listaEpisodi[0]

        if not (privato or offline):
            # Recupero informazioni anime in un Thread
            info_thread = Thread(target=provider.info_anime, args=[anime])
            info_thread.start()

        if downl:
            path = f"{downloadPath()}/{anime.name}"
            for ep in listaEpisodi:
                scaricaEpisodio(ep, path)
            ut.my_print(f"\nVideo scaricato correttamente!\nLo puoi trovare nella cartella {path}\n", color="verde")

            num, progress = episode.prev().num, anime.progress.get(episode.prev().num, 0) if episode.prev() else (0, 0)
            addToCronologia(num, progress)
                
            risp = fzf(["esci","indietro","guarda"])
            if risp == "esci":
                safeExit()
            if risp == "indietro":
                continue

        while True:
            voto_anilist = None
            if not (offline or privato) and "anilist" in ut.configData:
                executor = ThreadPoolExecutor(max_workers=1)
                voto_anilist = executor.submit(anilist.getAnimePrivateRating, ut.configData["anilist"]["token"], ut.configData["anilist"]["user_id"], anime.id_anilist)

            completed, progress = openVideos(episode)

            if not privato:
                if completed: 
                    progress = 0
                    #update watchlist anilist se ho fatto l'accesso
                    if voto_anilist:
                        updateAnilist(episode.numeric(), voto_anilist.result())

                anime.curr_ep = episode.num
                anime.progress[episode.num] = progress

                addToCronologia(anime.curr_ep, progress)   

            # menù che si visualizza dopo aver finito la riproduzione
            lista_menu = ["esci", "indietro"]

            if anime.last_ep != 1:
                lista_menu.append("seleziona")
            if episode.prev() or episode.numeric() > 1:
                lista_menu.append("antecedente")
            lista_menu.append("riguarda")
            if episode.next() or episode.num != anime.last_ep:
                lista_menu.append("prossimo")
    
            scelta_menu = fzf(lista_menu)

            if scelta_menu == "prossimo":
                if not episode.next():
                    provider.episodes(anime)
                episode = episode.next()    
            elif scelta_menu == "antecedente":
                if not episode.prev():
                    provider.episodes(anime)
                episode = episode.prev()
            elif scelta_menu == "seleziona":
                if len(anime.episodes()) == 1:
                    provider.episodes(anime)
                episode = scegliEpisodi()[0]
            elif scelta_menu == "indietro":
                break
            elif scelta_menu == "esci":
                safeExit()
        reload = True

log = []
scelta_anime = ""
openPlayer = None
notSelected = True
completeLimit = 90
provider = None

anime = Anime("", "")

if __name__ == "__main__":
    main()