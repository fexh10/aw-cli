import os
import mpv
import time
import hpcomt
import argparse
from pySmartDL import SmartDL
from pathlib import Path
from awcli.utilities import *


def RicercaAnime() -> list[Anime]:
    """dato in input un nome di un anime inserito dall'utente,\n
    restituisce un lista con gli url degli anime
    relativi alla ricerca"""

    while True:
        my_print("Cerca un anime\n>", color="magenta", cls=True, end=" ")
        scelta = input()
        # esco se metto exit
        if (scelta == "exit"):
            exit()

        risultati_ricerca = search(scelta)
        if (len(risultati_ricerca) != 0):
            break
        
        my_print("La ricerca non ha prodotto risultati", color="rosso")
        time.sleep(1)
    return risultati_ricerca


def scegliEpisodi() -> tuple[int, int]:
    """fa scegliere gli ep da guardare all'utente"""
    
    my_print(anime.name, cls=True)
    #se contiene solo 1 ep sarà riprodotto automaticamente
    if anime.ep == 1:
        return 1, 1

    if lista:
        return anime.ep, anime.ep

    # faccio decire all'utente il range di ep
    while True:
        if (nome_os == "Android"):
            my_print("Attenzione! Su Android non è ancora possibile specificare un range per lo streaming", color="giallo")
        my_print(f"Specifica un episodio, o per un range usa: ep_iniziale-ep_finale (Episodi: 1-{str(anime.ep)})\n>", color="magenta", end=" ")
        n_episodi = input()
        # controllo se l'utente ha inserito un range o un episodio unico (premere invio di default selezione automaticamente tutti gli episodi)
        if "-" not in n_episodi:
            if n_episodi == '':
                ep_iniziale = 1
                ep_finale = anime.ep
                break
            else:
                ep_iniziale = int(n_episodi)
                ep_finale = int(n_episodi)
                if (ep_iniziale > anime.ep or ep_iniziale < 1):
                    my_print("La ricerca non ha prodotto risultati", color="rosso")
                else:
                    break
        else:
            flag = 0
            temp1 = ""
            temp2 = ""
            for i in range(0, len(n_episodi)):
                if (flag == 0 and n_episodi[i] != '-'):
                    temp1 += n_episodi[i]
                if (n_episodi[i] == '-'):
                    flag = 1
                    continue
                if (flag == 1):
                    temp2 += n_episodi[i]

            ep_iniziale = int(temp1)
            ep_finale = int(temp2)
            if (ep_iniziale > ep_finale or ep_finale > anime.ep or ep_iniziale < 1):
                my_print("La ricerca non ha prodotto risultati", color="rosso")
            else:
                break

    return ep_iniziale, ep_finale


def downloadPath(create=True):
    if (nome_os == "Android"):
        path = f"storage/downloads/{anime.name}"
    else:
        path = f"{Path.home()}/Videos/Anime/{anime.name}"
    if create and not os.path.exists(path):
        os.makedirs(path)
    return path


def scaricaEpisodio(url_ep: str, path: str, nome_video: str):
    """utilizza la libreria PySmartDL
    per scaricare l'ep e lo salva in una cartella.
    se l'ep è già presente nella cartella non lo riscarica"""

    my_print("Preparo il download...", color="giallo")

    # se l'episodio non è ancora stato scaricato lo scarico, altrimenti skippo
    my_print(f"Episodio: {nome_video}", color="blu")
    if not os.path.exists(f"{path}/{nome_video}"):
        SDL = SmartDL(url_ep, f"{path}/{nome_video}")
        SDL.start()
    else:
        my_print("Episodio già scaricato, skippo...", color="giallo")


def open_Syncplay(url_ep: str):
    """avvia syncplay"""

    os.system(f"syncplay '{url_ep}' -a syncplay.pl:8999 --language it &>/dev/null")


def OpenPlayer(url_server: str, nome_video:str):
    """prende in input il link
    del video e apre il player per riprodurre il video"""

    if syncpl:
        open_Syncplay(url_server)
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


def openVideos(ep_iniziale: int,ep_finale: int):
    for ep in range(ep_iniziale, ep_finale+1):

        nome_video = f"{anime.name} Ep. {ep}"
        #se il video è già stato scaricato lo riproduco invece di farlo in streaming
        path = f"{downloadPath(create=False)}/{nome_video}"
        url_server = path if os.path.exists(path) else anime.getEpisodio(ep)
        my_print(f"Riproduco {nome_video}...", color="giallo", cls=True)
        OpenPlayer(url_server, nome_video)

def main():
    global syncpl
    global downl
    global lista
    global anime

    # args
    parser = argparse.ArgumentParser("aw-cli", description="Guarda anime dal terminale e molto altro!")
    if nome_os != "Android":
        parser.add_argument('-s', '--syncplay', action='store_true', dest='syncpl', help='usa syncplay per guardare un anime insieme ai tuoi amici')
    parser.add_argument('-d', '--download', action='store_true', dest='download', help='scarica gli episodi che preferisci')
    parser.add_argument('-l', '--lista', nargs='?', choices=['a', 's', 'd'], dest='lista', help='lista degli ultimi anime usciti su AnimeWorld. a = all, s = sub, d = dub')
    args = parser.parse_args()

    if nome_os != "Android":
        if args.syncpl:
            syncpl = True
    if args.download:
        downl = True
    elif args.lista:
        lista = True

    try:
        animes = latest(args.lista) if lista else RicercaAnime()
        while True:
            my_print("", end="", cls=True)
            # stampo i nomi degli anime
            for i, anime in reversed(list(enumerate(animes))):
                my_print(f"{i + 1} ", color="verde", end=" ")
                my_print(anime.name)
            
            while True:
                my_print("Scegli un anime\n>", color="magenta", end=" ")
                s = int(input())-1
                
                # controllo che il numero inserito sia giusto
                if s in range(len(animes)):
                    break
                my_print("Seleziona una risposta valida", color="rosso")
            
            anime = animes[s]
            anime.setUrlEpisodi()
            
            if anime.ep != 0:
                break

            # se l'anime non ha episodi non può essere selezionato
            my_print("Eh, volevi! L'anime non ha episodi", color="rosso")
            time.sleep(1)

        ep_iniziale, ep_finale = scegliEpisodi()

        # se syncplay è stato scelto allora non chiedo
        # di fare il download ed esco dalla funzione
        if not syncpl and downl:
            path = downloadPath()
            for ep in range(ep_iniziale, ep_finale+1):
                url_ep = anime.getEpisodio(ep)
                nome_video = f"{anime.name} Ep. {ep}"
                scaricaEpisodio(url_ep, path, nome_video)

            my_print("Tutti i video scaricati correttamente!\nLi puoi trovare nella cartella", color="verde", end=" ")
            if nome_os == "Android":
                my_print("Downloads", color="verde")
            else:
                my_print("Video/Anime", color="verde")
                
                #chiedi all'utente se aprire ora i video scaricati
                while True:
                    my_print("Aprire ora il player con gli episodi scaricati? (S/n)\n>", color="magenta", end=" ")
                    match input().lower():
                        case 's'|"": 
                            openVideos(ep_iniziale, ep_finale)
                            break
                        case 'n': break
                        case  _: my_print("Seleziona una risposta valida", color="rosso")
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
            if scelta_menu == 'p' and ep_iniziale < anime.ep:
                ep_iniziale = ep_finale + 1
                ep_finale = ep_iniziale
                continue
            elif scelta_menu == 'r':
                continue
            elif scelta_menu == 'a' and ep_iniziale > 1:
                ep_iniziale = ep_finale - 1
                ep_finale = ep_iniziale
                continue
            elif scelta_menu == 's':
                ep_iniziale, ep_finale = scegliEpisodi()
            elif scelta_menu == 'e' or scelta_menu == '':
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

if __name__ == "__main__":
    main()