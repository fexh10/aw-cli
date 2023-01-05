import os

if os.name == "nt":
    script_directory = os.path.dirname(os.path.realpath(__file__))
    os.environ["PATH"] = script_directory + os.pathsep + os.environ["PATH"]
    from pywinauto import Application
    import psutil

import mpv
import time
import hpcomt
import argparse
import warnings
import subprocess
import csv
from pySmartDL import SmartDL
from pathlib import Path
from awcli.utilities import *


def RicercaAnime() -> list[Anime]:
    """
    Dato in input un nome di un anime inserito dall'utente, restituisce una lista con gli URL degli anime
    relativi alla ricerca.

    Returns:
        list[Anime]: la lista con gli URL degli anime trovati
    """

    def check_search(s: str):
        if s == "exit":
            exit() 
        result = search(s)
        if len(result) != 0:
            return result

    my_print("", end="", cls=True)
    return my_input("Cerca un anime", check_search,"La ricerca non ha prodotto risultati", cls = True)
    

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

    if lista:
        return anime.ep, anime.ep

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
        path = f"storage/downloads"
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


def open_Syncplay(url_ep: str, nome_video: str):
    """
    Avvia Syncplay.

    Args:
        url_ep (str): l'URL dell'episodio da riprodurre.
        nome_video (str): il nome dell'episodio.
    """
    if os.name == "nt":
        pid = 0
        #avvio syncplay tramite l'exe e passo gli argomenti necessari
        comando = f"& 'C:\\Program Files (x86)\\Syncplay.\\Syncplay.exe' '{url_ep}' media-title='{nome_video}' -a syncplay.pl:8999"
        syncplay_exe =subprocess.Popen(['powershell.exe', comando])

        warnings.filterwarnings("ignore", category=UserWarning)
        #ricerco il PID di Syncplay.exe in modo da poter aspettare 
        #che venga chiuso per poter continuare con l'esecuzione del programma 
        PROCNAME = "Syncplay.exe"
        time.sleep(1)
        for proc in psutil.process_iter():
            if proc.name() == PROCNAME:
                pid = proc.pid
        app = Application().connect(process=pid)
        app.wait_for_process_exit(timeout=86400, retry_interval=0.1)
    else:
        os.system(f'''syncplay \"{url_ep}" media-title="{nome_video}" -a syncplay.pl:8999 --language it &>/dev/null''')


def OpenPlayer(url_server: str, nome_video: str):
    """
    Apre il player per riprodurre il video.

    Args:
        url_server (str): il link del video o il percorso del file.
        nome_video (str): il nome del video.
    """


    if syncpl:
        open_Syncplay(url_server, nome_video)
    elif (nome_os == "Android"):
        # apro il player utilizzando bash e riproduco un video
        # os.system("am start --user 0 -a android.intent.action.VIEW -d \"" +
        # url_server+"\" -n org.videolan.vlc/org.videolan.vlc.gui.video.VideoPlayerActivity -e \""+a.name+"ep "+str(a.ep)+"\" \"$trackma_title\" > /dev/null 2>&1 &")

        os.system("am start --user 0 -a android.intent.action.VIEW -d \"" +
                  url_server+"\" -n is.xyz.mpv/.MPVActivity > /dev/null 2>&1 &")
    else:
        player = mpv.MPV(input_default_bindings=True,
                         input_vo_keyboard=True, osc=True)

        # avvio il player
        player.fullscreen = True
        player.playlist_pos = 0
        player["keep-open"] = True
        player["media-title"] = nome_video
        player.play(url_server)
        player.wait_for_shutdown()
        player.terminate()


def checkCronologia(nome_file: str, nome_video: str) -> bool:
    """
    Controlli da fare prima di inserire un anime in cronologia.\n
    Se si sta riproducendo l'ultimo episodio di un anime, quest'ultimo viene rimosso dalla cronologia.\n
    Se l'anime è già presente nel file, la riga viene sostituita con il nuovo episodio.\n
    Se il file non esiste viene creato.

    Args:
        nome_file (str): il nome del file csv.
        nome_video (str): contiene il nome dell'anime e l'episodio visualizzato.

    Returns:
        flag (bool): assume valore True se l'anime è già presente, altrimenti False.
    """
    # creo il file se non esiste
    if not os.path.exists(nome_file):
        with open(nome_file, 'w') as csv_file:
            pass

    flag = False
    #apro il file in lettura per controllare se l'anime esiste già
    with open(nome_file, 'r') as csv_file_read:
        csv_reader = csv.reader(csv_file_read)
        nuove_righe = []
        for riga in csv_reader:
            #se l'ep riprodotto è l'ultimo allora non lo inserisco più
            if int(nome_video.split("Ep. ")[1]) == anime.ep:
                flag = True
                continue 
            #se l'anime è presente sovrascrivo la riga
            elif riga[1]== anime.url:
                flag = True
                nuova_riga = [nome_video, anime.url]
            else:
                nuova_riga = riga
            nuove_righe.append(nuova_riga)

    if flag:
        with open(nome_file, 'w', newline='') as csv_file_write:
            csv_writer = csv.writer(csv_file_write)
            csv_writer.writerows(nuove_righe)
    return flag


def addToCronologia(nome_video: str):
    """
    Viene aggiunta alla cronologia locale il nome del video
    e il link di AnimeWorld relativo all'anime.
    La cronologia viene salvata su un file csv nella stessa 
    directory dello script. Se il file non esiste viene creato.

    Args:
        nome_video (str): contiene il nome dell'anime e l'episodio visualizzato.
    """
    nome_file = f"{os.path.dirname(__file__)}/aw-cronologia.csv"
    esiste = checkCronologia(nome_file, nome_video)
    if not esiste:
        informazioni = []
        with open(nome_file, 'a', newline='') as csv_file:
            csv_writer = csv.writer(csv_file)
            informazioni = [nome_video, anime.url]
            csv_writer.writerow(informazioni)


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
        if offline:
            if os.path.exists(path):
                url_server = path
            else:
                my_print(f"Episodio {nome_video} non scaricato, skippo...", color='giallo')
                sleep(1)
                continue
        else:
            url_server = path if os.path.exists(path) else anime.get_episodio(ep)

        my_print(f"Riproduco {nome_video}...", color="giallo", cls=True)
        OpenPlayer(url_server, nome_video)
        #se non sono in modalità offline aggiungo l'anime alla cronologia
        if not offline:
            addToCronologia(nome_video)


def getCronologia() -> list[Anime]:
    """
    Prende i dati dalla cronologia.

    Returns:
        list[Anime]: la lista degli anime trovati
    """
    
    nome_file = f"{os.path.dirname(__file__)}/aw-cronologia.csv"
    #se il file non esiste stampo un messaggio di errore
    if not os.path.exists(nome_file):
        my_print("Cronologia inesistente!", color='rosso')
        exit()

    with open(nome_file, 'r') as csv_file_read:
        csv_reader = csv.reader(csv_file_read)
        animes = []
        for riga in csv_reader:
            animes.append(Anime(riga[0], riga[1]))
    #se il file esiste ma non contiene dati stampo un messaggio di errore
    if len(animes) == 0:
        my_print("Cronologia inesistente!", color='rosso')
        exit()
    return animes


def main():
    global syncpl
    global downl
    global lista
    global offline
    global cronologia
    global anime

    # args
    parser = argparse.ArgumentParser("aw-cli", description="Guarda anime dal terminale e molto altro!")
    if nome_os != "Android":
        parser.add_argument('-s', '--syncplay', action='store_true', dest='syncpl', help='usa syncplay per guardare un anime insieme ai tuoi amici')
    parser.add_argument('-d', '--download', action='store_true', dest='download', help='scarica gli episodi che preferisci')
    parser.add_argument('-l', '--lista', nargs='?', choices=['a', 's', 'd'], dest='lista', help='lista degli ultimi anime usciti su AnimeWorld. a = all, s = sub, d = dub')
    parser.add_argument('-o', '--offline', action='store_true', dest='offline', help='apri gli episodi scaricati precedentemente direttamente dal terminale')
    parser.add_argument('-c', '--cronologia', action='store_true', dest='cronologia', help='continua a guardare un anime dalla cronologia')
    args = parser.parse_args()

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

    try:
        animes = latest(args.lista) if lista else animeScaricati(downloadPath()) if offline else getCronologia() if cronologia else RicercaAnime()

        while True:
            my_print("", end="", cls=True)
            # stampo i nomi degli anime
            for i, anime in reversed(list(enumerate(animes))):
                my_print(f"{i + 1} ", color="verde", end=" ")
                my_print(anime.name)

            def check_index(s: str):
                if s.isdigit():
                    index = int(s) - 1
                    if index in range(len(animes)):
                        return index

            #scelta = my_input("Scegli un anime", lambda i: res if i.isdigit() and (res:=int(i)-1) in range(len(animes)) else None)
            scelta = my_input("Scegli un anime", check_index)
            anime = animes[scelta]

            anime.load_episodes() if not offline else anime.downloaded_episodes(f"{downloadPath()}/{anime.name}")

            if anime.ep != 0:
                break

            # se l'anime non ha episodi non può essere selezionato
            my_print("Eh, volevi! L'anime non ha episodi", color="rosso")
            time.sleep(1)

        if not cronologia:
            ep_iniziale, ep_finale = scegliEpisodi()
        else:
            ep_iniziale = int(anime.name.split("Ep. ")[1]) + 1
            ep_finale = ep_iniziale
            anime.name = anime.name.split(" Ep. ")[0]

        # se syncplay è stato scelto allora non chiedo
        # di fare il download ed esco dalla funzione
        if not syncpl and downl:
            path = f"{downloadPath()}/{anime.name}"
            for ep in range(ep_iniziale, ep_finale+1):
                scaricaEpisodio(ep, path)

            my_print("Tutti i video scaricati correttamente!\nLi puoi trovare nella cartella", color="verde", end=" ")
            if nome_os == "Android":
                my_print("Downloads", color="verde")
            else:
                my_print("Video/Anime", color="verde")
                
                #chiedi all'utente se aprire ora i video scaricati
                if my_input("Aprire ora il player con gli episodi scaricati? (S/n)", lambda i: i.lower()) in ['s', '']:
                    openVideos(ep_iniziale, ep_finale)
            exit()

        ris_valida = True
        while True:
            if ris_valida:
                openVideos(ep_iniziale,ep_finale)
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
                exit()
            else:
                my_print("", end="", cls=True)
                ris_valida = False

    except KeyboardInterrupt:
        exit()

# controllo il tipo del dispositivo
nome_os = hpcomt.Name()
#args
syncpl = False
downl = False
lista = False
offline = False
cronologia = False

anime = Anime("", "")

if __name__ == "__main__":
    main()