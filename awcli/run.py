import os

if os.name == "nt":
    script_directory = os.path.dirname(os.path.realpath(__file__))
    os.environ["PATH"] = script_directory + os.pathsep + os.environ["PATH"]

import mpv
import sys
import time
import hpcomt
import argparse
import warnings
import subprocess
import csv
from pySmartDL import SmartDL
from pathlib import Path
from awcli.utilities import *

def safeExit():
    with open(f"{os.path.dirname(__file__)}/aw-cronologia.csv", 'w', newline='') as file:
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
    my_print(nome_video, color="blu", end="")
    my_print(":\n" if nome_os == "Android" else ": ", end="")
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
    else:
        player = mpv.MPV(input_default_bindings=True,input_vo_keyboard=True, osc=True)

        # avvio il player
        player.fullscreen = True
        player.playlist_pos = 0
        player["keep-open"] = True
        player["media-title"] = nome_video
        player.play(url_server)
        player.wait_for_shutdown()
        player.terminate()


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
        comando = f"& 'C:\\Program Files\\VideoLAN\\VLC\\vlc.exe' '{url_server}' --fullscreen --meta-title='{nome_video}'"
        subprocess.Popen(['powershell.exe', comando])
        isRunning("vlc.exe")
    elif nome_os == "Android":
        os.system(f'''am start --user 0 -a android.intent.action.VIEW -d "{url_server}" -n org.videolan.vlc/.StartActivity -e "title" "{nome_video}" > /dev/null 2>&1 &''')    


def addToCronologia(ep: int):
    """
    Viene aggiunta alla cronologia locale il nome del video
    e il link di AnimeWorld relativo all'anime.
    La cronologia viene salvata su un file csv nella stessa 
    directory dello script. Se il file non esiste viene creato.

    Args:
        ep (int): il numero dell'episodio visualizzato.
    """
    for i, riga in enumerate(log):
        #se l'anime è presente
        if riga[2] == anime.url:
            #se l'ep riprodotto è l'ultimo allora non lo inserisco più
            if ep == anime.ep and anime.status == 1:
                log.pop(i)
            else: 
                #sovrascrivo la riga   
                log[i][1] = ep
            return
    if (ep == anime.ep and anime.status == 0) or ep != anime.ep:
        log.append([anime.name, ep, anime.url]) 


def openVideos(ep_iniziale: int, ep_finale: int, mpv: bool):
    """
    Riproduce gli episodi dell'anime, a partire da ep_iniziale fino a ep_finale.
    Se un episodio è già stato scaricato, viene riprodotto dal file scaricato.
    Altrimenti, viene riprodotto in streaming.

    Args:
        ep_iniziale (int): il numero di episodio iniziale da riprodurre.
        ep_finale (int): il numero di episodio finale da riprodurre.
        mpv (bool): True se il player di default è MPV, False se è VLC.
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
        openMPV(url_server, nome_video) if mpv else openVLC(url_server, nome_video)
        #se non sono in modalità offline aggiungo l'anime alla cronologia
        if not offline:
            addToCronologia(ep)


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
        episodi.append(riga[1])
        animes.append(Anime(riga[0], riga[2], riga[1]))
    #se il file esiste ma non contiene dati stampo un messaggio di errore
    if len(animes) == 0:
        my_print("Cronologia inesistente!", color='rosso')
        safeExit()
    return animes, episodi


def getConfig() -> bool:
    """
    Prende il nome del player scelto dal file di configurazione.

    Returns:
        bool: True se mpv è stato scelto, False se è stato scelto vlc.
    """

    config = f"{os.path.dirname(__file__)}/aw.config"
    with open(config, 'r') as config_file:
        for line in config_file:
            mpv = True if line == 'Player: MPV' else False
    return mpv


def main():
    global log
    global syncpl
    global downl
    global lista
    global offline
    global cronologia
    global anime
    try:
        with open(f"{os.path.dirname(__file__)}/aw-cronologia.csv") as file:
            log = [riga for riga in csv.reader(file)]
    except FileNotFoundError:
        pass
    # args
    parser = argparse.ArgumentParser("aw-cli", description="Guarda anime dal terminale e molto altro!")
    parser.add_argument('-c', '--cronologia', action='store_true', dest='cronologia', help='continua a guardare un anime dalla cronologia')
    parser.add_argument('-d', '--download', action='store_true', dest='download', help='scarica gli episodi che preferisci')
    parser.add_argument('-l', '--lista', nargs='?', choices=['a', 's', 'd'], dest='lista', help='lista degli ultimi anime usciti su AnimeWorld. a = all, s = sub, d = dub')
    parser.add_argument('-o', '--offline', action='store_true', dest='offline', help='apri gli episodi scaricati precedentemente direttamente dal terminale')
    if nome_os != "Android":
        parser.add_argument('-s', '--syncplay', action='store_true', dest='syncpl', help='usa syncplay per guardare un anime insieme ai tuoi amici')
    args = parser.parse_args()

    
    if  '-l' in sys.argv and args.lista == None:
        args.lista = 'a'

    if nome_os != "Android":
        if args.syncpl:
            syncpl = True
    if args.download:
        downl = True
    elif args.lista:
        lista = True
    elif args.offline:
        offline = True
    elif args.cronologia:
        cronologia = True

    mpv = getConfig()

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
                if lista or cronologia:
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
            anime.load_episodes() if not offline else anime.downloaded_episodes(f"{downloadPath()}/{anime.name}")

            if anime.ep != 0:
                break

            # se l'anime non ha episodi non può essere selezionato
            my_print("Eh, volevi! L'anime non ha episodi", color="rosso")
            time.sleep(1)

        if not cronologia:
            if not lista:
                ep_iniziale, ep_finale = scegliEpisodi()
        else:
            ep_iniziale = int(episodi[scelta]) + 1
            ep_finale = ep_iniziale
            if ep_finale > anime.ep:
                my_print(f"L'episodio {ep_iniziale} di {anime.name} non è ancora stato rilasciato!", color='rosso')
                exit()
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
                    openVideos(ep_iniziale, ep_finale, mpv)
            safeExit()

        ris_valida = True
        while True:
            if ris_valida:
                openVideos(ep_iniziale,ep_finale, mpv)
            else:
                my_print("Seleziona una risposta valida", color="rosso")
                ris_valida = True
            # menù che si visualizza dopo aver finito la riproduzione
            my_print("(p) prossimo", color="azzurro")
            my_print("(r) riguarda", color="blu")
            my_print("(a) antecedente", color="azzurro")
            my_print("(s) seleziona", color="verde")
            my_print("(e) esci", color="rosso")
            my_print(">", color="magenta", end=" ")
            scelta_menu = input().lower()
            if (scelta_menu == 'p' or scelta_menu == '') and ep_iniziale < anime.ep - (ep_finale - ep_iniziale):
                ep_iniziale = ep_finale + 1
                ep_finale = ep_iniziale
                continue
            elif scelta_menu == 'r':
                continue            
            elif scelta_menu == 'a' and ep_finale > anime.ep_ini:
                ep_iniziale = ep_finale - 1
                ep_finale = ep_iniziale
                continue
            elif scelta_menu == 's':
                ep_iniziale, ep_finale = scegliEpisodi()
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
log = []

anime = Anime("", "")

if __name__ == "__main__":
    main()