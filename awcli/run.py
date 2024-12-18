import os
import csv
import concurrent.futures
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


def fzf(elementi: list[str], prompt: str = "> ", cls: bool = False, esci: bool = True) -> str:
    """
    Avvia fzf con impostazioni predefinite.

    Args:
        elementi (list[str]): lista da passare ad fzf con gli elementi da selezionare.
        prompt (str, optional): il prompt che fzf deve stampare. Valore predefinito: "> ".
        cls (bool, optional): se impostato a True, pulisce lo schermo prima di stampare il testo. Valore predefinito: False.
        esci (bool, optional): se True, esce dal programma se l'input dell'utente è vuoto. Valore predefinito: True.

    Returns:
        str: la scelta selezionata tramite fzf.
    """

    if cls:
        my_print("",end="", cls=True)
    string = "\n".join(elementi)
    comando = f"""fzf --tac --height={len(elementi) + 2} --cycle --ansi --tiebreak=begin --prompt="{prompt}" """
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


def scegliEpisodi() -> int:
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

    return int(fzf(ep, "Scegli un episodio: "))


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


def openSyncplay(url_ep: str, nome_video: str):
    """
    Avvia Syncplay.

    Args:
        url_ep (str): l'URL dell'episodio da riprodurre.
        nome_video (str): il nome dell'episodio.
    """

    if syncplay_path == "Syncplay: None":
        my_print("Aggiornare il path di syncplay nella configurazione tramite: aw-cli -a", color="rosso")
        safeExit()

    os.system(f''''{syncplay_path}' "{url_ep}" force-media-title="{nome_video}" --language it > /dev/null 2>&1''')


def openMPV(url_ep: str, nome_video: str) -> int:
    """
    Apre MPV per riprodurre il video.

    Args:
        url_server (str): il link del video o il percorso del file.
        nome_video (str): il nome del video.

    Returns:
        int: il progresso percentuale dell'episodio visualizzato.
    """


    if (nome_os == "Android"):
        os.system(f'''am start --user 0 -a android.intent.action.VIEW -d "{url_ep}" -n is.xyz.mpv/.MPVActivity > /dev/null 2>&1''')
        return
    
    out = os.popen(f"""'{player_path}' "{url_ep}" --force-media-title="{nome_video}" --fullscreen --keep-open --start="{anime.progress}" 2>&1""")

    res = re.findall(r'AV: (\d+:\d+:\d+) / [\d:]+ \((\d+)%\)', out.read())[-1]
    
    time = res[0].split(":")
    anime.progress = (int(time[0]) * 3600) + (int(time[1]) * 60) + int(time[2])
    
    return int(res[1]) 


def openVLC(url_ep: str, nome_video: str):
    """
    Apre VLC per riprodurre il video.

    Args:
        url_server (str): il link del video o il percorso del file.
        nome_video (str): il nome del video.
    """

    if nome_os == "Android":
        os.system(f'''am start --user 0 -a android.intent.action.VIEW -d "{url_ep}" -n org.videolan.vlc/.StartActivity -e "title" "{nome_video}" > /dev/null 2>&1''')    
        return
    
    os.system(f''''{player_path}' "{url_ep}" --meta-title "{nome_video}" --fullscreen --start-time="{anime.progress}"> /dev/null 2>&1''')

def addToCronologia(ep: int, progress: int = 0):
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
    - progresso dell'episodio visualizzato

    Args:
        ep (int): il numero dell'episodio visualizzato.
    """
    
    #rimuovo l'anime dalla cronologia se è già presente
    for i, riga in enumerate(log):
        if riga[0] == anime.name:
            log.pop(i)
            break
            
    if ep == anime.ep and anime.status == 1 and progress >= completeLimit:
        return
    #aggiungo l'anime alla cronologia con i nuovi dati  
    new = [anime.name, ep, anime.url, anime.ep_totali, anime.status, anime.ep, anime.id_anilist, anime.progress]

    if ep == anime.ep and progress >= completeLimit:
        new[7] = 0
        log.append(new)
    else:
        if progress < completeLimit:
            new[1] -= 1
        log.insert(0, new)


def updateAnilist(ep: int, drop: bool = False):
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
    status_list = 'CURRENT'
    
    if drop:
        status_list = 'DROPPED'

    #se ho finito di vedere l'anime o lo stato è dropped    
    if (ep == anime.ep and anime.status == 1) or status_list == 'DROPPED':
        if status_list == 'CURRENT':
            status_list = 'COMPLETED'
    
        #chiedo di votare
        if anilist.ratingAnilist:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                def is_number(n):
                    try:
                        return float(n)
                    except ValueError:
                        pass
                future_voto = executor.submit(my_input,f"Inserisci un voto per l'anime", is_number)
                #ottengo il voto dell'anime se già inserito in precedenza
                future_rating = executor.submit(anilist.getAnimePrivateRating, anime.id_anilist)
                voto_anilist = future_rating.result()

                if int(voto_anilist) != 0:
                    my_print(f"Riproduco {anime.name} Ep. {anime.ep}", color="giallo", cls=True)
                    my_print(f"Inserisci un voto per l'anime (voto corrente: {voto_anilist}): ", end=" ", color="ciano", bg_color="ciano_bg")
                voto = future_voto.result()
    
        #chiedo di mettere tra i preferiti
        if anilist.preferitoAnilist and status_list == 'COMPLETED':
            my_print(f"Riproduco {anime.name} Ep. {anime.ep}", color="giallo", cls=True)
            preferiti = fzf(["sì","no"], "Mettere l'anime tra i preferiti? ")
    
    if preferiti: 
        thread = Thread(target=anilist.addToAnilistFavourite, args=(anime.id_anilist, ep, voto))
    else:
        thread = Thread(target=anilist.addToAnilist, args=(anime.id_anilist, ep, status_list, voto))

    thread.start()


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

    my_print(f"Riproduco {nome_video}...", color="giallo", cls=True)
    if ep != anime.ep_corrente+1:
        anime.progress = 0

    progress = openPlayer(url_ep, nome_video)
    if progress == None:
        progress = completeLimit

    anime.ep_corrente = ep if progress >= completeLimit else ep-1
    

    if offline or privato: return

    addToCronologia(ep, progress) 

    #update watchlist anilist se ho fatto l'accesso
    if anilist.tokenAnilist != 'tokenAnilist: False' and progress >= completeLimit:
        updateAnilist(ep)


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
        a.progress = int(riga[7])
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
    try:
        #player predefinito
        my_print("", end="", cls=True)
        my_print("AW-CLI - CONFIGURAZIONE", color="giallo")

        player = fzf(["vlc","mpv"], "Scegli il player predefinito: ")
        if nome_os != "Linux" and nome_os != "Android":
            player = my_input("Inserisci il path del player")
            my_print("AW-CLI - CONFIGURAZIONE", color="giallo", cls=True)

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
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(anilist.getAnilistUserId)
                my_print("AW-CLI - CONFIGURAZIONE", color="giallo", cls=True)
                if fzf(["sì","no"], "Votare l'anime una volta completato? ") == "sì":
                    ratingAnilist = "ratingAnilist: True "
                    
                if fzf(["sì","no"], "Chiedere se mettere l'anime tra i preferiti una volta completato? ") == "sì":
                    preferitoAnilist = "preferitoAnilist: True"
                
                if fzf(["sì","no"], "Chiedere se droppare l'anime una volta rimosso dalla cronologia? ") == "sì":
                    dropAnilist = "dropAnilist: True"
                
                anilist.user_id = future.result()

        if nome_os == "Linux":
            syncplay= "syncplay"
        elif nome_os == "Android": 
                syncplay = "Syncplay: None"
        else:
            syncplay = my_input("Inserisci il path di Syncplay (premere INVIO se non lo si desidera utilizzare)")
            if syncplay == "":
                syncplay = "Syncplay: None"
    except KeyboardInterrupt:
        safeExit()
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
        os.system(f"kill {pid[len(pid) - 1]}")
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
                    updateAnilist(anime.ep_corrente, True)

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
    global syncpl
    global downl
    global lista
    global offline
    global cronologia
    global info
    global privato
    global anime
    global player_path
    global syncplay_path
    global openPlayer
    global scelta_anime
    global notSelected
    global completeLimit

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

   
    openPlayer = openMPV if mpv else openVLC

    if nome_os != "Android" and args.syncpl:
        openPlayer = openSyncplay

    while True:
        try:
            if cronologia:
                animelist = getCronologia()
            elif lista:
                animelist = latest(args.lista)
            elif offline:
                animelist = animeScaricati(downloadPath())
            else:
                animelist = RicercaAnime()
                
            while True:
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

                if args.cronologia == 'r':
                    anime = animelist[scelta]
                    removeFromCrono(scelta)
                    animelist = getCronologia()
                    continue
                
                anime = animelist[scelta]
                #se la lista è stata selezionata, inserisco come ep_iniziale quello scelto dall'utente
                #succcessivamente anime.ep verrà sovrascritto con il numero reale dell'episodio finale
                if lista:
                    ep_iniziale = anime.ep
                scelta_info = ""
                scelta_download = False

                anime.load_info() if not offline else downloaded_episodes(anime,f"{downloadPath()}/{anime.name}")

                if info:
                    anime.print_info()
                    #stampo piccolo menu
                    scelta_info = fzf(["indietro","guardare"])
                    if  scelta_info== "indietro":
                        break

                if anime.ep != 0:
                    break

                # se l'anime non ha episodi non può essere selezionato
                my_print("Eh, volevi! L'anime non è ancora stato rilasciato", color="rosso")
                sleep(1)
            #se ho l'args -i e ho scelto di tornare indietro, faccio una continue sul ciclo while True
            if scelta_info == "indietro":
                continue
            
            if cronologia:            
                ep_iniziale = anime.ep_corrente + 1
                if ep_iniziale > anime.ep:
                    my_print(f"L'episodio {ep_iniziale} di {anime.name} non è ancora stato rilasciato!", color='rosso')
                    if len(log) == 1:
                        safeExit()
                    sleep(1)
                    continue
            while not lista and not cronologia:
                ep_iniziale = scegliEpisodi()
                anime.ep_corrente = ep_iniziale - 1
                if not downl:
                    break
                
                if downl:
                    path = f"{downloadPath()}/{anime.name}"
                    scaricaEpisodio(ep_iniziale, path)

                    my_print("\nVideo scaricato correttamente!\nLo puoi trovare nella cartella", color="verde", end=" ")
                    if nome_os == "Android":
                        my_print("Movies/Anime\n", color="verde")
                    else:
                        my_print("Video/Anime\n", color="verde")
                        
                        risp = fzf(["esci","indietro","guarda","continua"])
                        if risp == "esci":
                            safeExit()
                        elif risp == "guarda":
                            break   
                        elif risp == "continua":
                            continue
                        elif risp == "indietro":
                            scelta_download = True
                            break
            
            if scelta_download:
                scelta_download = False
                continue

            while True:
                openVideos(ep_iniziale)

                prossimo = True
                antecedente = True
                seleziona = True
                # menù che si visualizza dopo aver finito la riproduzione
                lista_menu = ["esci", "indietro"]

                if anime.ep != 1:
                    lista_menu.append("seleziona")
                else:
                    seleziona = False
                if ep_iniziale != anime.ep_ini:
                    lista_menu.append("antecedente")
                else:
                    antecedente = False
                lista_menu.append("riguarda")
                if ep_iniziale != anime.ep:
                    lista_menu.append("prossimo")
                else:
                    prossimo = False
        
                scelta_menu = fzf(lista_menu)

                if scelta_menu == "prossimo" and prossimo:
                    ep_iniziale += 1
                    continue
                elif scelta_menu == "riguarda":
                    continue            
                elif scelta_menu == "antecedente" and antecedente:
                    ep_iniziale -= 1
                    continue
                elif scelta_menu == "seleziona" and seleziona:
                    ep_iniziale = scegliEpisodi()
                elif scelta_menu == "indietro":
                    break
                elif scelta_menu == "esci":
                    safeExit()

        except KeyboardInterrupt:
            safeExit()

log = []
player_path = ""
syncplay_path = ""
scelta_anime = ""
openPlayer = None
notSelected = True
completeLimit = 90

anime = Anime("", "")

if __name__ == "__main__":
    main()