import os
import sys
import time
import hpcomt
import argparse
import warnings
import subprocess
import csv
import concurrent.futures
from pySmartDL import SmartDL
from pathlib import Path
from threading import Thread
from awcli.utilities import *

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


def isRunning(PROCNAME: str):
    """
    Viene preso il pid di un processo per poter attendere 
    che l'applicazione venga chiusa prima di poter proseguire
    con il programma. Viene impostato un timeout di 86400 secondi (24 ore).

    Args:
        PROCNAME (str): il nome del processo.
    """

    import psutil
    from pywinauto import Application

    sleep(1)
    pid = 0
    for proc in psutil.process_iter():
        if proc.name() == PROCNAME:
            pid = proc.pid
    app = Application().connect(process=pid)
    app.wait_for_process_exit(timeout=86400)


def open_Syncplay(url_ep: str, nome_video: str):
    """
    Avvia Syncplay.

    Args:
        url_ep (str): l'URL dell'episodio da riprodurre.
        nome_video (str): il nome dell'episodio.
    """
    if os.name == "nt":
        #avvio syncplay tramite l'exe e passo gli argomenti necessari
        comando = f"& 'C:\\Program Files (x86)\\Syncplay.\\Syncplay.exe' '{url_ep}' media-title='{nome_video}'"
        subprocess.Popen(['powershell.exe', comando])
        warnings.filterwarnings("ignore", category=UserWarning)
        isRunning("Syncplay.exe")
    else:
        os.system(f'''syncplay \"{url_ep}" media-title="{nome_video}" --language it &>/dev/null''')


def openMPV(url_server: str, nome_video: str):
    """
    Apre MPV per riprodurre il video.

    Args:
        url_server (str): il link del video o il percorso del file.
        nome_video (str): il nome del video.
    """

    if syncpl:
        open_Syncplay(url_server, nome_video)
    elif (nome_os == "Android"):
        # apro il player utilizzando bash e riproduco un video
        os.system(f'''am start --user 0 -a android.intent.action.VIEW -d "{url_server}" -n is.xyz.mpv/.MPVActivity > /dev/null 2>&1 &''')
    elif nome_os == "Windows":
        import mpv
        
        player = mpv.MPV(input_default_bindings=True,input_vo_keyboard=True, osc=True)

        # avvio il player
        player.fullscreen = True
        player.playlist_pos = 0
        player["keep-open"] = True
        player["media-title"] = nome_video
        player.play(url_server)
        player.wait_for_shutdown()
        player.terminate()
    elif nome_os == "Linux":
        os.system(f'''mpv "{url_server}" --force-media-title="{nome_video}" --fullscreen --keep-open &>/dev/null''')


def openVLC(url_server: str, nome_video: str):
    """
    Apre VLC per riprodurre il video.

    Args:
        url_server (str): il link del video o il percorso del file.
        nome_video (str): il nome del video.
    """

    if nome_os == 'Linux':
        os.system(f'''vlc "{url_server}" --meta-title "{nome_video}" --fullscreen &>/dev/null''')
    elif nome_os == "Windows":
        comando = f"""& 'C:\\Program Files\\VideoLAN\\VLC\\vlc.exe' "{url_server}" --fullscreen --meta-title="{nome_video}" """
        subprocess.Popen(['powershell.exe', comando])
        isRunning("vlc.exe")
    elif nome_os == "Android":
        os.system(f'''am start --user 0 -a android.intent.action.VIEW -d "{url_server}" -n org.videolan.vlc/.StartActivity -e "title" "{nome_video}" > /dev/null 2>&1 &''')    


def addToCronologia(ep: int):
    """
    Viene aggiunta alla cronologia locale il nome del video,
    il numero dell'ultimo episodio visualizzato,
    il link di AnimeWorld relativo all'anime
    e il numero reale di episodi totali della serie.
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
                temp = log.pop(i)
                temp[-1] = anime.ep_totali
                #se l'anime è in corso e l'ep visualizzato è l'ultimo, metto l'anime alla fine della cronologia
                if anime.status == 0 and ep == anime.ep:
                    log.insert(len(log), temp)
                #altrimenti all'inizio
                else:
                    log.insert(0, temp)
            return
    if (ep == anime.ep and anime.status == 0) or ep != anime.ep:
        if anime.status == 0 and ep == anime.ep:
            log.insert(len(log), [anime.name, ep, anime.url, anime.ep_totali])
        else:
            log.insert(0, [anime.name, ep, anime.url, anime.ep_totali]) 


def updateAnilist(tokenAnilist: str, ratingAnilist: bool, preferitoAnilist: bool,  ep: int, voto_anilist: str):
    """
    Procede ad aggiornare l'anime su AniList.
    Se l'episodio riprodotto è l'ultimo e
    l'utente ha scelto di votare gli anime,
    verrà chiesto il voto da dare.

    Args:
        tokenAnilist (str): il token di accesso ad AniList.
        ratingAnilist (bool): valore impostato a True se l'utente ha scelto di votare l'anime una volta finito, altrimenti False.
        preferitoAnilist(bool): True se l'utente ha scelto di far chiedere se mettere l'anime tra i preferiti, altrimenti False.
        ep (int): il numero dell'episodio visualizzato.
        voto_anilist (str): il voto dato dall'utente all'anime su Anilist.
    """

    voto = 0
    preferiti = False
    status_list = 'CURRENT'
    #se ho finito di vedere l'anime
    if ep == anime.ep and anime.status == 1:
        status_list = 'COMPLETED'
        #chiedo di votare
        if ratingAnilist:
            def is_number(n):
                if n.isdigit():
                    return n

            voto = my_input(f"Inserisci un voto per l'anime (voto corrente: {voto_anilist})", is_number)
    
            voto = float(voto)
        #chiedo di mettere tra i preferiti
        if preferitoAnilist:
            def check_string(s: str):
                s = s.lower()
                if s == "s":
                    return True
                elif s == "n" or s == "":
                    return False

            preferiti = my_input("Mettere l'anime tra i preferiti? (s/N)", check_string)
    
    thread = Thread(target=anilistApi, args=(tokenAnilist, anime.id_anilist, ep, voto, status_list, preferiti))
    thread.start()


def openVideos(ep_iniziale: int, ep_finale: int, mpv: bool, tokenAnilist: str, ratingAnilist: bool, preferitoAnilist: bool, user_id: int):
    """
    Riproduce gli episodi dell'anime, a partire da ep_iniziale fino a ep_finale.
    Se un episodio è già stato scaricato, viene riprodotto dal file scaricato.
    Altrimenti, viene riprodotto in streaming.

    Args:
        ep_iniziale (int): il numero di episodio iniziale da riprodurre.
        ep_finale (int): il numero di episodio finale da riprodurre.
        mpv (bool): True se il player di default è MPV, False se è VLC.
        tokenAnilist (str): il token di accesso ad AniList.
        ratingAnilist (bool): valore impostato a True se l'utente ha scelto di votare l'anime una volta finito, altrimenti False.
        preferitoAnilist(bool): True se l'utente ha scelto di far chiedere se mettere l'anime tra i preferiti, altrimenti False.
    """

    for ep in range(ep_iniziale, ep_finale+1):

        nome_video = anime.ep_name(ep)
        #se il video è già stato scaricato lo riproduco invece di farlo in streaming
        path = f"{downloadPath(create=False)}/{anime.name}/{nome_video}.mp4"
        
        if os.path.exists(path):
            url_server = "file://" + path if nome_os == "Android" else path
        elif offline:
            my_print(f"Episodio {nome_video} non scaricato, skippo...", color='giallo')
            sleep(1)
            continue
        else:
            url_server = anime.get_episodio(ep)

        my_print(f"Riproduco {nome_video}...", color="giallo", cls=True)

        #se è l'episodio finale e l'utente deve votare l'anime, controllo se l'id è presente
        # e ottengo il voto dell'anime se già inserito in precedenza
        #prendo l'id dell'utente tramite query
        voto_anilist = "n.d."
        if ep == anime.ep and ratingAnilist == True and not offline and not privato:         
            #prendo il voto se presente
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future_rating = executor.submit(getAnimePrivateRating, tokenAnilist, user_id, anime.id_anilist)
                voto_anilist = future_rating.result()

        openMPV(url_server, nome_video) if mpv else openVLC(url_server, nome_video)

        #se non sono in modalità offline o privata aggiungo l'anime alla cronologia
        if not offline and not privato:
            addToCronologia(ep)

        #update watchlist anilist se ho fatto l'accesso
        if tokenAnilist != 'tokenAnilist: False' and not offline and not privato:
            updateAnilist(tokenAnilist, ratingAnilist, preferitoAnilist, ep, voto_anilist)


def getCronologia() -> tuple[list, list]:
    """
    Prende i dati dalla cronologia.

    Returns:
        tuple[list, list]: una tupla con la lista degli anime trovati e
        la lista degli ultimi episodi visualizzati.

    """
    episodi = []
    animes = []
    for riga in log:
        if len(riga) == 3:
            riga.append("??")
        episodi.append(riga[1])
        animes.append(Anime(riga[0], riga[2], riga[1], riga[3]))

    #se il file esiste ma non contiene dati stampo un messaggio di errore
    if len(animes) == 0:
        my_print("Cronologia inesistente!", color='rosso')
        safeExit()
    return animes, episodi


def setupConfig() -> None:
    """
    Crea un file di configurazione chiamato "aw.config"
    nella stessa directory dello script.
    Le informazioni riportate saranno scelte dall'utente.
    Sarà possibile scegliere il Player predefinito
    e se collegare il proprio profilo AniList. 
    """
    try:
        #player predefinito
        my_print("", end="", cls=True)
        my_print("AW-CLI - CONFIGURAZIONE", color="giallo")
        my_print("1", color="verde", end="  ")
        my_print("MPV")
        my_print("2", color="verde", end="  ")
        my_print("VLC")

        def check_index(s: str):
            if s == "1":
                return "Player: MPV"
            elif s == "2":
                return "Player: VLC"

        player = my_input("Scegli un player predefinito", check_index)

        #animelist
        def check_string(s: str):
            s = s.lower()
            if s == "s":
                return True
            elif s == "n" or s == "":
                return False

        anilist = my_input("Aggiornare automaticamente la watchlist con AniList? (s/N)", check_string)

        if anilist:
            if nome_os == "Linux" or nome_os == "Android":
                os.system("xdg-open 'https://anilist.co/api/v2/oauth/authorize?client_id=11388&response_type=token' &>/dev/null")
            elif nome_os == "Windows":
                subprocess.Popen(['powershell.exe', "explorer https://anilist.co/api/v2/oauth/authorize?client_id=11388&response_type=token"])
            #inserimento token
            tokenAnilist = my_input("Inserire il token di AniList", cls=True)
            #chiede se votare l'anime
            if my_input("Votare l'anime una volta completato? (s/N)", check_string):
                ratingAnilist = "ratingAnilist: True "
                #prendo l'id dell'utente tramite query
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(getAnilistUserId, tokenAnilist)
                    user_id = future.result()
            else:
                ratingAnilist = "ratingAnilist: False"
                user_id = 0
            preferitoAnilist = "preferitoAnilist: True" if my_input("Chiedere se mettere l'anime tra i preferiti una volta completato? (s/N)", check_string) else "preferitoAnilist: False"

        else:
            tokenAnilist = "tokenAnilist: False"
            ratingAnilist = "ratingAnilist: False"
            preferitoAnilist = "preferitoAnilist: False"
            user_id = 0
    except KeyboardInterrupt:
        safeExit()
    #creo il file
    config = f"{os.path.dirname(__file__)}/aw.config"
    with open(config, 'w') as config_file:
        config_file.write(f"{player}\n")
        config_file.write(f"{tokenAnilist}\n")
        config_file.write(f"{ratingAnilist}\n")
        config_file.write(f"{preferitoAnilist}\n")
        config_file.write(f"{user_id}")


def getConfig() -> tuple[bool, str, bool, bool, int]:
    """
    Prende le impostazioni scelte dall'utente
    dal file di configurazione.

    Returns:
        tuple[bool, str, bool, int]: mpv ritorna True se è stato scelto mpv, altrimenti false se è VLC.
        tokenAnilist ritorna il token di Anilist se è stato inserito. ratingAnilist ritorna True
        se l'utente ha scelto di votare gli anime, altrimenti False. preferitoAnilist ritorna
        True se l'utente ha scelto di chiedere se l'anime deve essere aggiunto tra i preferiti,
        altrimenti False. user_id ritorna l'id dell'utente.  
    """

    config = f"{os.path.dirname(__file__)}/aw.config"
    with open(config, 'r+') as config_file:
        lines = config_file.readlines()
        mpv = True if lines[0].strip() == "Player: MPV" else False
        tokenAnilist = lines[1].strip()
        ratingAnilist = True if lines[2].strip() == "ratingAnilist: True" else False
        preferitoAnilist = True if lines[3].strip() == "preferitoAnilist: True" else False
        if len(lines) == 4 and ratingAnilist == False:
            user_id = 0
        elif len(lines) == 4 and ratingAnilist == True:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(getAnilistUserId, tokenAnilist)
                    user_id = future.result()
                    config_file.write(f"{user_id}")
        else:
            user_id = lines[4]

    return mpv, tokenAnilist, ratingAnilist, preferitoAnilist, user_id


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
    try:
        with open(f"{os.path.dirname(__file__)}/aw-cronologia.csv", encoding='utf-8') as file:
            log = [riga for riga in csv.reader(file)]
    except FileNotFoundError:
        pass
    # args
    parser = argparse.ArgumentParser("aw-cli", description="Guarda anime dal terminale e molto altro!")
    parser.add_argument('-a', '--configurazione', action='store_true', dest='avvia_config', help='avvia il menu di configurazione')
    parser.add_argument('-c', '--cronologia', action='store_true', dest='cronologia', help='continua a guardare un anime dalla cronologia')
    parser.add_argument('-d', '--download', action='store_true', dest='download', help='scarica gli episodi che preferisci')
    parser.add_argument('-i', '--info', action='store_true', dest='info', help='visualizza le informazioni e la trama di un anime')
    parser.add_argument('-l', '--lista', nargs='?', choices=['a', 's', 'd'], dest='lista', help='lista degli ultimi anime usciti su AnimeWorld. a = all, s = sub, d = dub')
    parser.add_argument('-o', '--offline', action='store_true', dest='offline', help='apri gli episodi scaricati precedentemente direttamente dal terminale')
    parser.add_argument('-p', '--privato', action='store_true', dest='privato', help="guarda un episodio senza che si aggiorni la cronologia o AniList")

    if nome_os != "Android":
        parser.add_argument('-s', '--syncplay', action='store_true', dest='syncpl', help='usa syncplay per guardare un anime insieme ai tuoi amici')
    args = parser.parse_args()


    if  '-l' in sys.argv and args.lista == None:
        args.lista = 'a'

    if nome_os != "Android":
        if args.syncpl:
            syncpl = True
    if args.avvia_config:
        setupConfig()
    if args.info:
        info = True
    if args.download:
        downl = True
    if args.lista:
        lista = True
    if args.privato:
        privato = True
    elif args.offline:
        offline = True
    elif args.cronologia:
        cronologia = True

    #se il file di configurazione non esiste viene chiesto all'utente di fare il setup
    if not os.path.exists(f"{os.path.dirname(__file__)}/aw.config"):
        setupConfig()
    mpv, tokenAnilist, ratingAnilist, preferitoAnilist, user_id = getConfig()

    while True:
        try:
            if not cronologia:
                animelist = latest(args.lista) if lista else animeScaricati(downloadPath()) if offline else RicercaAnime()
            else:
                animelist, episodi = getCronologia()

            while True:
                my_print("", end="", cls=True)
                # stampo i nomi degli anime
                for i, a in reversed(list(enumerate(animelist))):
                    my_print(f"{i + 1} ", color="verde", end=" ")
                    if cronologia:
                        my_print(f"{a.name} [Ep {a.ep}/{a.ep_totali}]")
                    elif lista:
                       my_print(f"{a.name} [Ep {a.ep}]") 
                    else:
                        my_print(a.name)

                def check_index(s: str):
                    if s.isdigit():
                        index = int(s) - 1
                        if index in range(len(animelist)):
                            return index
                
                scelta = my_input("Scegli un anime", check_index)
                anime = animelist[scelta]
                #se la lista è stata selezionata, inserisco come ep_iniziale e ep_finale quello scelto dall'utente
                #succcessivamente anime.ep verrà sovrascritto con il numero reale dell'episodio finale
                if lista:
                    ep_iniziale = anime.ep
                    ep_finale = ep_iniziale
                scelta_info = ""
                if info:
                    scelta_info = anime.getAnimeInfo()
                    if scelta_info == 'i':
                        break
                anime.load_episodes(tokenAnilist) if not offline else anime.downloaded_episodes(f"{downloadPath()}/{anime.name}")

                if anime.ep != 0:
                    break

                # se l'anime non ha episodi non può essere selezionato
                my_print("Eh, volevi! L'anime non è ancora stato rilasciato", color="rosso")
                time.sleep(1)
            #se ho l'args -i e ho scelto di tornare indietro, faccio una continue sul ciclo while True
            if scelta_info == 'i':
                continue
            if not cronologia:
                if not lista:
                    ep_iniziale, ep_finale = scegliEpisodi()
            else:
                ep_iniziale = int(episodi[scelta]) + 1
                ep_finale = ep_iniziale
                if ep_finale > anime.ep:
                    my_print(f"L'episodio {ep_iniziale} di {anime.name} non è ancora stato rilasciato!", color='rosso')
                    if len(log) == 1:
                        exit()
                    else:
                        sleep(1)
                        continue
            # se syncplay è stato scelto allora non chiedo
            # di fare il download ed esco dalla funzione
            if not syncpl and downl:
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
                        openVideos(ep_iniziale, ep_finale, mpv, tokenAnilist, ratingAnilist, preferitoAnilist, user_id)
                safeExit()

            ris_valida = True
            while True:
                if ris_valida:
                    openVideos(ep_iniziale,ep_finale, mpv, tokenAnilist, ratingAnilist, preferitoAnilist, user_id)
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

# controllo il tipo del dispositivo
nome_os = hpcomt.Name()
#args
syncpl = False
downl = False
lista = False
offline = False
cronologia = False
info = False
privato = False
log = []

anime = Anime("", "")

if __name__ == "__main__":
    main()