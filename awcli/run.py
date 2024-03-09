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


def scegliEpisodi() -> tuple[int, int]:
    """
    Fa scegliere all'utente gli episodi dell'anime da guardare.

    Se l'anime ha solo un episodio, questo verrà riprodotto automaticamente.
    In caso contrario, l'utente può scegliere un singolo episodio o un intervallo di episodi da riprodurre.
    Inserire il valore predefinito (Enter) farà riprodurre tutti gli episodi disponibili.

    Returns:
        tuple[int, int]: una tupla con il numero di episodio iniziale e finale da riprodurre.
    """

    
    my_print(anime.name, cls=True)
    #se contiene solo 1 ep sarà riprodotto automaticamente
    if anime.ep == 1:
        return 1, 1

    # faccio decire all'utente il range di ep
    if (nome_os == "Android"):
        my_print("Attenzione! Su Android non è ancora possibile specificare un range per lo streaming", color="giallo")
    # controllo se l'utente ha inserito un range o un episodio unico
    def check_string(s: str):
        if s.isdigit():
            n = int(s)
            if n in range(anime.ep_ini, anime.ep+1):
                return n,n
        elif "-" in s:
            n, m = s.split("-")
            if not n.isdigit() or not m.isdigit():
                return None
            n = int(n)
            m = int(m)
            if n in range(anime.ep_ini, anime.ep+1) and m in range(n, anime.ep+1):
                return n, m
        elif s == "":
            return anime.ep_ini, anime.ep

    return my_input(f"Specifica un episodio, o per un range usa: ep_iniziale-ep_finale (Episodi: {anime.ep_ini}-{anime.ep})",check_string,"Ep. o range selezionato non valido")


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

    os.system(f''''{syncplay_path}' "{url_ep}" media-title="{nome_video}" --language it > /dev/null 2>&1''')


def openMPV(url_ep: str, nome_video: str):
    """
    Apre MPV per riprodurre il video.

    Args:
        url_server (str): il link del video o il percorso del file.
        nome_video (str): il nome del video.
    """


    if (nome_os == "Android"):
        os.system(f'''am start --user 0 -a android.intent.action.VIEW -d "{url_ep}" -n is.xyz.mpv/.MPVActivity > /dev/null 2>&1''')
        return
    
    os.system(f"""'{player_path}' "{url_ep}" --force-media-title="{nome_video}" --fullscreen --keep-open > /dev/null 2>&1""")


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
    
    os.system(f''''{player_path}' "{url_ep}" --meta-title "{nome_video}" --fullscreen > /dev/null 2>&1''')


def addToCronologia(ep: int):
    """
    Viene aggiunta alla cronologia locale il nome del video,
    il numero dell'ultimo episodio visualizzato,
    il link di AnimeWorld relativo all'anime, 
    il numero reale di episodi totali della serie, lostato dell'anime
    e l'id anilist.
    La cronologia viene salvata su un file csv nella stessa 
    directory dello script. Se il file non esiste viene creato.

    Args:
        ep (int): il numero dell'episodio visualizzato.
    """
    for i, riga in enumerate(log):
        #se l'anime è presente
        if riga[0] == anime.name:
            #se l'ep riprodotto è l'ultimo allora non lo inserisco più
            if ep == anime.ep and anime.status == 1:
                log.pop(i)
            else: 
                #sovrascrivo la riga   
                log[i][1] = ep
                log[i][2] = anime.url
                log[i][3] = anime.ep_totali
                log[i][4] = anime.status
                log[i][5] = anime.ep
                log[i][6] = anime.id_anilist
                temp = log.pop(i)
                #se l'anime è in corso e l'ep visualizzato è l'ultimo, metto l'anime alla fine della cronologia
                if anime.status == 0 and ep == anime.ep:
                    log.insert(len(log), temp)
                #altrimenti all'inizio
                else:
                    log.insert(0, temp)
            return
    if (ep == anime.ep and anime.status == 0) or ep != anime.ep:
        if anime.status == 0 and ep == anime.ep:
            log.insert(len(log), [anime.name, ep, anime.url, anime.ep_totali, anime.status, anime.ep, anime.id_anilist])
        else:
            log.insert(0, [anime.name, ep, anime.url, anime.ep_totali, anime.status, anime.ep, anime.id_anilist]) 


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
                    my_print(f"Inserisci un voto per l'anime (voto corrente: {voto_anilist})\n> ", end=" ", color="magenta", cls=True)
                voto = future_voto.result()
    
        #chiedo di mettere tra i preferiti
        if anilist.preferitoAnilist and status_list == 'COMPLETED':
            def check_string(s: str):
                s = s.lower()
                if s == "s":
                    return True
                elif s == "n" or s == "":
                    return False

            preferiti = my_input("Mettere l'anime tra i preferiti? (s/N)", check_string)
    
    if preferiti: 
        thread = Thread(target=anilist.addToAnilistFavourite, args=(anime.id_anilist, ep, voto))
    else:
        thread = Thread(target=anilist.addToAnilist, args=(anime.id_anilist, ep, status_list, voto))

    thread.start()


def openVideos(ep_iniziale: int, ep_finale: int):
    """
    Riproduce gli episodi dell'anime, a partire da ep_iniziale fino a ep_finale.
    Se un episodio è già stato scaricato, viene riprodotto dal file scaricato.
    Altrimenti, viene riprodotto in streaming.

    Args:
        ep_iniziale (int): il numero di episodio iniziale da riprodurre.
        ep_finale (int): il numero di episodio finale da riprodurre.
    """

    for ep in range(ep_iniziale, ep_finale+1):

        nome_video = anime.ep_name(ep)
        #se il video è già stato scaricato lo riproduco invece di farlo in streaming
        path = f"{downloadPath(create=False)}/{anime.name}/{nome_video}.mp4"
        
        if os.path.exists(path):
            url_ep = "file://" + path if nome_os == "Android" else path
        elif offline:
            my_print(f"Episodio {nome_video} non scaricato, skippo...", color='giallo')
            sleep(1)
            continue
        else:
            url_ep = anime.get_episodio(ep)

        my_print(f"Riproduco {nome_video}...", color="giallo", cls=True)
        openPlayer(url_ep, nome_video)
        if offline or privato: return

        addToCronologia(ep)

        #update watchlist anilist se ho fatto l'accesso
        if anilist.tokenAnilist != 'tokenAnilist: False':
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
        a = Anime(name=riga[0], url=riga[2], ep=int(riga[5]), ep_totali=riga[3])
        a.ep_corrente = int(riga[1])
        a.status = int(riga[4])
        a.id_anilist = int(riga[6])
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
        
        player = "vlc" 

        #animelist
        def check_string(s: str):
            s = s.lower()
            if s == "s":
                return True
            elif s == "n" or s == "":
                return False
            
        ratingAnilist = "ratingAnilist: False"
        preferitoAnilist = "preferitoAnilist: False"
        dropAnilist = "dropAnilist: False"
        
        if my_input("Aggiornare automaticamente la watchlist con AniList? (s/N)", check_string):
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
                
                if my_input("Votare l'anime una volta completato? (s/N)", check_string):
                    ratingAnilist = "ratingAnilist: True "
                    
                if my_input("Chiedere se mettere l'anime tra i preferiti una volta completato? (s/N)", check_string):
                    preferitoAnilist = "preferitoAnilist: True"
                
                if my_input("Chiedere se droppare l'anime una volta rimosso dalla cronologia? (s/N)", check_string):
                    dropAnilist = "dropAnilist: True"
                
                anilist.user_id = future.result()

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
    if 0 not in [anime.status for anime in cronologia]:
        return
    
    my_print("Ricerco le nuove uscite...", color="giallo")
    ultime_uscite = latest()
    my_print(end="", cls=True)
                
    for i, a in reversed(list(enumerate(cronologia))):
        colore = "rosso"
        if a.status == 1 or a.ep_corrente < a.ep:
            colore = "verde"
        else:    
            for anime_latest in ultime_uscite:
                if a.name == anime_latest.name and a.ep_corrente < anime_latest.ep:
                    log[i][5] = anime_latest.ep
                    colore = "verde"
                    break
                
        my_print(f"{i + 1} ", color=colore, end=" ")
        my_print(f"{a.name} [Ep {a.ep_corrente}/{a.ep_totali}]")
        
    my_print("Scegli un anime\n> ", end=" ", color="magenta")


def printAnimeNames(animelist: list[Anime]): 
    """
    Stampa i nomi degli anime presenti nella lista desiderata.

    Args:
        animelist (list[Anime]): Una lista Anime.    

    Return: 
        None. 
    """

    my_print("", end="", cls=True)

    colore = "verde"

    for i, a in reversed(list(enumerate(animelist))):
        if cronologia:
            colore = "rosso"
            if a.status == 1 or a.ep_corrente < a.ep:
                colore = "verde"
        
        my_print(f"{i + 1} ", color=colore, end=" ")
        if cronologia:
            my_print(f"{a.name} [Ep {a.ep_corrente}/{a.ep_totali}]")
        elif lista:
            my_print(f"{a.name} [Ep {a.ep}]") 
        else:
            my_print(a.name)


def removeFromCrono(number: int):
    """
    Rimuove l'anime selezionato dalla cronologia
    e stampa un menu di scelta per l'utente.

    Args:
        number (int): il numero dell'anime in lista da rimuovere.

    Return:
        None.
    """

    def check_yes(s: str):
        s.lower()
        if s == "s":
            return True
        elif s == "n" or s == "":
            return False

    global log

    my_print(f"Si è sicuri di voler rimuovere \"{anime.name}\" dalla cronologia? (s/N)", color="giallo", end="")
    delete = my_input("", check_yes)

    if delete:
        if anilist.dropAnilist:
            drop = my_input(f"Droppare \"{anime.name}\" su AniList? (s/N)", check_yes)

            if drop:
                updateAnilist(anime.ep_corrente, True)

        log.pop(number)

        printAnimeNames(getCronologia())

        def check_str(s: str):
            s.lower()
            if s == "c" or s== "e" or s == '':
                return s

        my_print("(c) continua", color="verde")
        my_print("(e) esci", color="rosso", end="")
        scelta = my_input("", check_str)

        if scelta == "e" or scelta == '':
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
    openPlayer = lambda url_ep, nome_video: os.system(f"printf \"\e]8;;vlc://%s\a~~~~~~~~~~~~~~~~~~~~\n~ Premi per aprire VLC ~\n~~~~~~~~~~~~~~~~~~~~\e]8;;\a\n\" \"{url_ep}\"")

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
                printAnimeNames(animelist)

                if cronologia and args.cronologia != 'r':
                    thread = Thread(target=reloadCrono, args=[animelist])    
                    thread.start()

                def check_index(s: str):
                    if s.isdigit():
                        index = int(s) - 1
                        if index in range(len(animelist)):
                            return index
                
                if args.cronologia == 'r':
                    scelta = my_input("Rimuovi un anime", check_index)
                    anime = animelist[scelta]
                    removeFromCrono(scelta)
                    animelist = getCronologia()
                    continue
                
                scelta = my_input("Scegli un anime", check_index)

                anime = animelist[scelta]
                #se la lista è stata selezionata, inserisco come ep_iniziale e ep_finale quello scelto dall'utente
                #succcessivamente anime.ep verrà sovrascritto con il numero reale dell'episodio finale
                if lista:
                    ep_iniziale = anime.ep
                    ep_finale = ep_iniziale
                scelta_info = ""

                anime.load_info() if not offline else downloaded_episodes(anime,f"{downloadPath()}/{anime.name}")

                if info:
                    anime.print_info()
                    #stampo piccolo menu
                    def check_string(s: str):
                        s.lower()
                        if s == "g" or s == 'i' or s == "":
                            return s

                    my_print("(g) guardare", color='verde')
                    my_print("(i) indietro", color='magenta', end="")
                    scelta_info = my_input("", check_string)
                    if scelta_info == 'i':
                        break

                if anime.ep != 0:
                    break

                # se l'anime non ha episodi non può essere selezionato
                my_print("Eh, volevi! L'anime non è ancora stato rilasciato", color="rosso")
                sleep(1)
            #se ho l'args -i e ho scelto di tornare indietro, faccio una continue sul ciclo while True
            if scelta_info == 'i':
                continue

            if cronologia:            
                ep_iniziale = anime.ep_corrente + 1
                ep_finale = ep_iniziale
                if ep_finale > anime.ep:
                    my_print(f"L'episodio {ep_iniziale} di {anime.name} non è ancora stato rilasciato!", color='rosso')
                    if len(log) == 1:
                        safeExit()
                    sleep(1)
                    continue
            elif not lista:
                ep_iniziale, ep_finale = scegliEpisodi()
            
            if downl:
                path = f"{downloadPath()}/{anime.name}"
                for ep in range(ep_iniziale, ep_finale+1):
                    scaricaEpisodio(ep, path)

                my_print("Tutti i video scaricati correttamente!\nLi puoi trovare nella cartella", color="verde", end=" ")
                if nome_os == "Android":
                    my_print("Movies/Anime", color="verde")
                else:
                    my_print("Video/Anime", color="verde")
                    
                    #chiedi all'utente se aprire ora i video scaricati
                    if my_input("Aprire ora il player con gli episodi scaricati? (S/n)", lambda i: i.lower()) in ['s', '']:
                        openVideos(ep_iniziale, ep_finale)
                safeExit()

            ris_valida = True
            while True:
                if ris_valida:
                    openVideos(ep_iniziale,ep_finale)
                else:
                    my_print("Seleziona una risposta valida", color="rosso")
                    ris_valida = True

                prossimo = True
                antecedente = True
                seleziona = True

                # menù che si visualizza dopo aver finito la riproduzione
                if ep_finale != anime.ep:
                    my_print("(p) prossimo", color="azzurro")
                else:
                    prossimo = False
                my_print("(r) riguarda", color="blu")
                if ep_finale != anime.ep_ini:
                    my_print("(a) antecedente", color="azzurro")
                else:
                    antecedente = False
                if anime.ep != 1:
                    my_print("(s) seleziona", color="verde")
                else:
                    seleziona = False
                my_print("(i) indietro", color='magenta')
                my_print("(e) esci", color="rosso")
                my_print(">", color="magenta", end=" ")
                scelta_menu = input().lower()
                if (scelta_menu == 'p' or scelta_menu == '') and prossimo:
                    ep_iniziale = ep_finale + 1
                    ep_finale = ep_iniziale
                    continue
                elif scelta_menu == 'r':
                    continue            
                elif scelta_menu == 'a' and antecedente:
                    ep_iniziale = ep_finale - 1
                    ep_finale = ep_iniziale
                    continue
                elif scelta_menu == 's' and seleziona:
                    ep_iniziale, ep_finale = scegliEpisodi()
                elif scelta_menu == 'i':
                    break
                elif scelta_menu == 'e':
                    safeExit()
                else:
                    my_print("", end="", cls=True)
                    ris_valida = False

        except KeyboardInterrupt:
            safeExit()

log = []
player_path = ""
syncplay_path = ""
openPlayer = None

anime = Anime("", "")

if __name__ == "__main__":
    main()