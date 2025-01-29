import os
import csv
from signal import signal, SIGINT
from concurrent.futures import ThreadPoolExecutor
from pySmartDL import SmartDL
from pathlib import Path
from threading import Thread
from awcli.utilities import * 
from awcli.arg_parser import *
import awcli.anilist as anilist

def safeExit():
    with open(f"{os.path.dirname(__file__)}/aw-cronologia.csv", 'w', newline='', encoding='utf-8') as file:
        csv.writer(file).writerows(log)
    exit()

signal(SIGINT, safeExit)

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
        my_print("",end="", cls=True)
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
        result = search(s)
        if len(result) != 0:
            return result

    my_print("", end="", cls=True)
    return my_input("Cerca un anime", check_search,"La ricerca non ha prodotto risultati", cls = True)


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
        my_print("Nessun anime scaricato", color='rosso')
        safeExit()

    animes = list[Anime]()
    for name in nomi:
        animes.append(Anime(name, f"{path}/{name}"))
    return animes


def scegliEpisodi() -> list[int]:
    """
    Fa scegliere all'utente gli episodi dell'anime da guardare.

    Se l'anime ha solo un episodio, questo verrà riprodotto automaticamente.
    In caso contrario, l'utente può scegliere un episodio.

    Returns:
        int: il numero dell'episodio da riprodurre.
    """

    
    my_print(anime.name, cls=True)
    #se contiene solo 1 ep sarà riprodotto automaticamente
    if anime.ep == 1:
        return 1

    ep = [str(i) for i in range(anime.ep, anime.ep_ini - 1, -1)] 
    return sorted([int(ep) for ep in fzf(ep, "Scegli un episodio: ", multi=downl).split("\n")])


def downloadPath(create: bool = True) -> str:
    """
    Restituisce il percorso di download dell'anime, a seconda del sistema operativo in uso.
    Se create è True (valore predefinito) e il percorso non esiste, viene creato.

    Args:
        create (bool, optional): se impostato a True, crea il percorso se non esiste. Valore predefinito: True.

    Returns:
        str: il percorso di download dell'anime.
    """

    if (nome_os == "Android"):
        path = f"/sdcard/Movies/Anime"
    else:
        path = f"{Path.home()}/Videos/Anime"
    if create and not os.path.exists(path):
        os.makedirs(path)
    return path


def scaricaEpisodio(ep: int, path: str):
    """
    Scarica l'episodio dell'anime e lo salva nella cartella specificata.
    Se l'episodio è già presente nella cartella, non viene riscaricato.

    Args:
        ep (int): il numero dell'episodio da scaricare.
        path (str): il percorso dove salvare l'episodio.
    """

    url_ep = anime.get_episodio(ep)
    nome_video = anime.ep_name(ep)
    
    # se l'episodio non è ancora stato scaricato lo scarico, altrimenti skippo
    my_print(nome_video, color="blu", end=":\n")
    if not os.path.exists(f"{path}/{nome_video}.mp4"):
        SDL = SmartDL(url_ep, f"{path}/{nome_video}.mp4")
        SDL.start()
    else:
        my_print("già scaricato, skippo...", color="giallo")

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

    if syncplay_path == "Syncplay: None":
        my_print("Aggiornare il path di syncplay nella configurazione tramite: aw-cli -a", color="rosso")
        safeExit()
    
    
    args = f'''--force-media-title="{nome_video}" --start="{progress}" --fullscreen --keep-open'''
    if not mpv:
        args = f'''--meta-title "{nome_video}" --start-time="{progress}" --fullscreen'''
    
    try :
        out = os.popen(f'''{syncplay_path} -d --language it "{url_ep}" -- {args} 2>&1''').read()
    except UnicodeDecodeError:
        out = ""

    duration_match = re.findall(r'duration(?:-change)?"?: (\d+)\.?[\d]*', out)
    progress_match = re.findall(r'pos(?:ition"?)?:? (\d+).?\d+', out)
    if not duration_match:
        my_print("Errore, impossibile leggere l'output di Syncplay!", color="rosso")
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


    if (nome_os == "Android"):
        os.system(f'''am start --user 0 -a android.intent.action.VIEW -d "{url_ep}" -n is.xyz.mpv/.MPVActivity > /dev/null 2>&1''')
        return True, 0

    out = os.popen(f'''{player_path} "{url_ep}" --force-media-title="{nome_video}" --start="{progress}" --fullscreen --keep-open 2>&1''')

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

    if nome_os == "Android":
        os.system(f'''am start --user 0 -a android.intent.action.VIEW -d "{url_ep}" -n org.videolan.vlc/.StartActivity -e "title" "{nome_video}" > /dev/null 2>&1''')    
        return True, 0
    
    os.system(f'''{player_path} "{url_ep}" --meta-title "{nome_video}" --start-time="{progress}" --fullscreen > /dev/null 2>&1''')

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
    
    tmp = anime.ep_len.split()
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
        if riga[0] == anime.name:
            log.pop(i)
            break
            
    if ep == anime.ep and anime.status == 1:
        return
    #aggiungo l'anime alla cronologia con i nuovi dati  
    new = [anime.name, ep, anime.url, anime.ep_totali, anime.status, anime.ep, anime.id_anilist, progress]

    if ep == anime.ep:
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
        my_print("Impossibile aggiornare AniList: id anime non trovato!", color="rosso")
        return
    
    voto = 0
    preferiti = False
    status_list = 'CURRENT' if not drop else 'DROPPED'

    #se ho finito di vedere l'anime o lo stato è dropped    
    if (ep == anime.ep and anime.status == 1) or status_list == 'DROPPED':
        if status_list == 'CURRENT':
            status_list = 'COMPLETED'
    
        #chiedo di votare
        if anilist.ratingAnilist:
            is_number = lambda n: float(n) if n.replace('.', '', 1).isdigit() else None
            voto = my_input("Inserisci un voto per l'anime" + (f" (voto corrente: {voto_anilist})" if voto_anilist else ""), is_number)
    
        #chiedo di mettere tra i preferiti
        if anilist.preferitoAnilist and status_list == 'COMPLETED':
            my_print(f"Riproduco {anime.name} Ep. {anime.ep}", color="giallo", cls=True)
            preferiti = fzf(["sì","no"], "Mettere l'anime tra i preferiti? ") == "sì"
    
    Thread(target=anilist.updateAnilist, args=(anime.id_anilist, ep, status_list, voto, preferiti)).start()


def openVideos(ep: int):
    """
    Riproduce l'episodio dell'anime.
    Se un episodio è già stato scaricato, viene riprodotto dal file scaricato.
    Altrimenti, viene riprodotto in streaming.

    Args:
        ep (int): il numero di episodio da riprodurre.
    """

    nome_video = anime.ep_name(ep)
    #se il video è già stato scaricato lo riproduco invece di farlo in streaming
    path = f"{downloadPath(create=False)}/{anime.name}/{nome_video}.mp4"
    
    if os.path.exists(path):
        url_ep = "file://" + path if nome_os == "Android" else path
    elif offline:
        my_print(f"Episodio {nome_video} non scaricato, skippo...", color='giallo')
        return
    else:
        url_ep = anime.get_episodio(ep)
    
    if not (offline or privato) and anilist.tokenAnilist != 'tokenAnilist: False':
        executor = ThreadPoolExecutor(max_workers=1)
        voto_anilist = executor.submit(anilist.getAnimePrivateRating, anime.id_anilist)

    my_print(f"Riproduco {nome_video}...", color="giallo", cls=True)
    progress = anime.progress[ep]
    openPlayer(url_ep, nome_video, progress)
    completed = True
    if privato: return

    if completed: 
        progress = 0
        anime.ep_corrente = ep
        #update watchlist anilist se ho fatto l'accesso
        if not offline and anilist.tokenAnilist != 'tokenAnilist: False':
            updateAnilist(ep, voto_anilist.result())
    else:
        anime.ep_corrente = ep - 1
    anime.progress[ep] = progress

    addToCronologia(anime.ep_corrente, progress)     


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
        a = Anime(name=riga[0], url=riga[2], ep=int(riga[5]), ep_totali=riga[3])
        a.ep_corrente = int(riga[1])
        a.status = int(riga[4])
        a.id_anilist = int(riga[6])
        a.progress[a.ep_corrente+1] = int(riga[7])
        animes.append(a)

    #se il file esiste ma non contiene dati stampo un messaggio di errore
    if len(animes) == 0:
        my_print("Cronologia inesistente!", color='rosso')
        safeExit()
    return animes


def setupConfig() -> None:
    """
    Crea un file di configurazione chiamato "aw.config"
    nella stessa directory dello script.
    Le informazioni riportate saranno scelte dall'utente.
    Sarà possibile scegliere il Player predefinito, 
    se collegare il proprio profilo AniList e 
    se inserire il path di syncplay.  
    """
    #player predefinito
    my_print("", end="", cls=True)
    my_print("AW-CLI - CONFIGURAZIONE", color="giallo")
    
    player = "vlc" 

    #animelist
    ratingAnilist = "ratingAnilist: False"
    preferitoAnilist = "preferitoAnilist: False"
    dropAnilist = "dropAnilist: False"
    
    if fzf(["sì","no"], "Aggiornare automaticamente la watchlist con AniList? ") == "sì":
        link = "https://anilist.co/api/v2/oauth/authorize?client_id=11388&response_type=token"
        if nome_os == "Linux" or nome_os == "Android":
            os.system(f"xdg-open '{link}' > /dev/null 2>&1")
        else: 
            os.system(f"open '{link}' > /dev/null 2>&1")

        #inserimento token
        anilist.tokenAnilist = my_input(f"Inserire il token di AniList ({link})", cls=True)
        
        #prendo l'id dell'utente tramite query
        with ThreadPoolExecutor() as executor:
            future = executor.submit(anilist.getAnilistUserId)
            my_print("AW-CLI - CONFIGURAZIONE", color="giallo", cls=True)
            if fzf(["sì","no"], "Votare l'anime una volta completato? ") == "sì":
                ratingAnilist = "ratingAnilist: True "
                
            if fzf(["sì","no"], "Chiedere se mettere l'anime tra i preferiti una volta completato? ") == "sì":
                preferitoAnilist = "preferitoAnilist: True"
            
            if fzf(["sì","no"], "Chiedere se droppare l'anime una volta rimosso dalla cronologia? ") == "sì":
                dropAnilist = "dropAnilist: True"
            
            anilist.user_id = future.result()

    syncplay = "Syncplay: None"
        
    #creo il file
    config = f"{os.path.dirname(__file__)}/aw.config"
    with open(config, 'w') as config_file:
        config_file.write(f"{player}\n{anilist.tokenAnilist}\n{ratingAnilist}\n{preferitoAnilist}\n{dropAnilist}\n{anilist.user_id}\n{syncplay}")


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
    
    if 0 not in [anime.status for anime in cronologia]:
        return
    
    my_print("Ricerco le nuove uscite...", color="giallo")
    ultime_uscite = latest()
    my_print(end="", cls=True)
    testo = []

    for i, a in reversed(list(enumerate(cronologia))):
        colore = 1 #2 verde, 1 rosso
        if a.status == 1 or a.ep_corrente < a.ep:
            colore = 2
        else:    
            for anime_latest in ultime_uscite:
                if a.name == anime_latest.name and a.ep_corrente < anime_latest.ep:
                    log[i][5] = anime_latest.ep
                    colore = 2
                    break
        testo.append(f"\033[0;3{colore}m{i + 1}  \033[0;37m{a.name} [Ep {a.ep_corrente}/{a.ep_totali}]")
    
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
        if cronologia:
            colore = 1
            if a.status == 1 or a.ep_corrente < a.ep:
                colore = 2
        
        nome = f"\033[0;3{colore}m{i + 1}  \033[0;37m"

        if cronologia:
            nome += f"{a.name} [Ep {a.ep_corrente}/{a.ep_totali}]"
        elif lista:
            nome += f"{a.name} [Ep {a.ep}]" 
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

    delete = fzf(["sì","no"], f"Si è sicuri di voler rimuovere {anime.name} dalla cronologia? ")

    if delete == "sì":
        if anilist.dropAnilist:
            drop = fzf(["sì","no"], f"Droppare {anime.name} su AniList? ")

            if drop == "sì":
                if anime.id_anilist == 0:
                    my_print("Impossibile droppare su AniList: id anime non trovato!", color="rosso")
                    sleep(1)
                else:
                    updateAnilist(anime.ep_corrente, drop=True)

        log.pop(number)

        scelta = fzf(["esci","continua"], cls=True)

        if scelta == "esci":
            safeExit()


def updateScript():
    """
    Aggiorna di default il programma in base 
    all'ultima versione stabile.
    Se viene specificato il branch,
    verrà installato quest'ultimo.
    """

    if args.update == None:
        comando = "echo y | python3 -m pip uninstall aw-cli > /dev/null 2>&1 && python3 -m pip install aw-cli > /dev/null 2>&1"
    else: 
        comando = f"echo y | python3 -m pip uninstall aw-cli > /dev/null 2>&1 && python3 -m pip install git+https://github.com/fexh10/aw-cli.git@{args.update} > /dev/null 2>&1"

    os.system(comando)
    
    my_print("aw-cli aggiornato con successo!", color="bianco")
    exit()


def main():
    global log
    global anime
    global player_path
    global syncplay_path
    global openPlayer
    global scelta_anime
    global notSelected
    global mpv

    if update:
        updateScript()

    try:
        with open(f"{os.path.dirname(__file__)}/aw-cronologia.csv", encoding='utf-8') as file:
            log = [riga for riga in csv.reader(file)]
    except FileNotFoundError:
        pass
    
    #se il file di configurazione non esiste viene chiesto all'utente di fare il setup
    if args.avvia_config or not os.path.exists(f"{os.path.dirname(__file__)}/aw.config"):
        setupConfig()

    mpv, player_path, syncplay_path = getConfig()
    #se la prima riga del config corrisponde a una versione vecchia, faccio rifare il config
    if player_path.startswith("Player") or mpv == None:
        my_print("Ci sono stati dei cambiamenti nella configurazione...", color="giallo")
        sleep(1)
        setupConfig()
        mpv, player_path, syncplay_path = getConfig()

   
    #openPlayer = openMPV if mpv else openVLC
    openPlayer = lambda url_ep, nome_video, progress: os.system(f"printf \"\e]8;;vlc://%s\a~~~~~~~~~~~~~~~~~~~~\n~ Premi per aprire VLC ~\n~~~~~~~~~~~~~~~~~~~~\e]8;;\a\n\" \"{url_ep}\"")

    reload = True
    while True:
        if reload:
            if cronologia:
                animelist = getCronologia()
            elif lista:
                animelist = latest(args.lista)
            else:
                animelist = RicercaAnime()
            if offline:
                animelist = [anime for anime in animelist if anime.name in [a.name for a in animeScaricati(downloadPath())]]

        my_print("", end="", cls=True)
        esci = True
        if cronologia and args.cronologia != 'r':
            notSelected = True 
            thread = Thread(target=reloadCrono, args=[animelist])    
            thread.start()
            esci = False
        
        prompt = "Rimuovi un anime: " if args.cronologia == 'r' else "Scegli un anime: "                
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

        anime.load_info() if not offline else downloaded_episodes(anime,f"{downloadPath()}/{anime.name}")

        if info:
            anime.print_info()
            #stampo piccolo menu per scegliere se guardare l'anime o tornare indietro
            if fzf(["indietro","guardare"]) == "indietro":
                continue

        if anime.ep == 0:
            my_print("Eh, volevi! L'anime non è ancora stato rilasciato", color="rosso")
            sleep(1)
            reload = False
            continue          
        
        if lista or cronologia:            
            listaEpisodi = [anime.ep_corrente + 1]
        else:
            listaEpisodi = scegliEpisodi()
            anime.ep_corrente = listaEpisodi[0] - 1

        if listaEpisodi[0] > anime.ep:
            my_print(f"L'episodio {listaEpisodi[0]} di {anime.name} non è ancora stato rilasciato!", color='rosso')
            sleep(1)
            if len(animelist) == 1:
                safeExit()
            reload = False
            continue

        if not privato:
            addToCronologia(anime.ep_corrente, anime.progress[anime.ep_corrente + 1])
            
        if downl:
            path = f"{downloadPath()}/{anime.name}"
            for ep in listaEpisodi:
                scaricaEpisodio(ep, path)

            my_print(f"\nVideo scaricato correttamente!\nLo puoi trovare nella cartella {path}\n", color="verde")
                
            risp = fzf(["esci","indietro","guarda"])
            if risp == "esci":
                safeExit()
            if risp == "indietro":
                continue
        
        episodio = listaEpisodi[0]
        while True:
            openVideos(episodio)

            # menù che si visualizza dopo aver finito la riproduzione
            lista_menu = ["esci", "indietro"]

            if anime.ep != 1:
                lista_menu.append("seleziona")
            if episodio != anime.ep_ini:
                lista_menu.append("antecedente")
            lista_menu.append("riguarda")
            if episodio != anime.ep:
                lista_menu.append("prossimo")
    
            scelta_menu = fzf(lista_menu)

            if scelta_menu == "prossimo":
                episodio = episodio + 1      
            elif scelta_menu == "antecedente":
                episodio = episodio - 1
            elif scelta_menu == "seleziona":
                episodio = scegliEpisodi()[0]
            elif scelta_menu == "indietro":
                break
            elif scelta_menu == "esci":
                safeExit()
        reload = True

log = []
player_path = ""
syncplay_path = ""
scelta_anime = ""
openPlayer = None
notSelected = True
completeLimit = 90
mpv = True

anime = Anime("", "")

if __name__ == "__main__":
    main()