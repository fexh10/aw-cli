import os
from bs4 import BeautifulSoup
import requests
import mimetypes
import mpv
import time
from pySmartDL import SmartDL
from pathlib import Path
import hpcomt
import argparse
from awcli.utilities import *
from awcli.animeworld import AnimeWorld


def listaUscite(selected: str) -> list[Anime]:
    """scraping per le ultime uscite di anime se AW"""

    url_ricerca = "https://www.animeworld.tv"
    contenuto_html = requests.get(url_ricerca).text
    bs = BeautifulSoup(contenuto_html, "lxml")

    animes = list[Anime]()

    match selected:
        case 's': data_name = "sub"
        case 'd': data_name = "dub"
        case  _ : data_name = "all"
        

    div = bs.find("div", {"data-name": data_name})
    for div in div.find_all(class_='inner'):
        anime = Anime()
        anime.url = "https://www.animeworld.tv" + div.a.get('href')
        
        for a in div.find_all(class_='name'):
            anime.name = a.text
        for div in div.find_all(class_='ep'):
            anime.name += " [" + div.text + "]"
        
        animes.append(anime)

    return animes


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

        risultati_ricerca = sito.search(scelta)
        if (len(risultati_ricerca) != 0):
            break
        
        my_print("La ricerca non ha prodotto risultati", color="rosso")
        time.sleep(1)
    return risultati_ricerca


def UrlEpisodi(url: str) -> list[str]:
    """prende in input l'url dell'anime scelto dall'utente\n
    restituisce: gli url di tutti gli episodi"""

    # prendo l'html dalla pagina web di AW
    html_content = requests.get(url).text
    soup = BeautifulSoup(html_content, "lxml")
    url_episodi = []
    # cerco gli url di tutti gli episodi
    for div in soup.find_all(class_='server active'):
        for li in div.find_all(class_="episode"):
            temp = "https://www.animeworld.tv" + (li.a.get('href'))
            url_episodi.append(temp)
    return url_episodi

def trovaUrlServer(url_ep: str) -> str:
    # creo un obj BS con la pagina dell'ep
    html = requests.get(url_ep).text
    sp = BeautifulSoup(html, "lxml")

    # variabile temp per capire in che posizione è l'url tra tutti gli url della pagina
    j = 0
    # ciclo for con il numoro totale degli url
    for url in TrovaUrl(str(sp)):
        # se l'url è un video e si trova in posizione 1 allora è quello del server
        if (mimetypes.MimeTypes().guess_type(url)[0] == 'video/mp4'):
            if (j == 1):
                return url
            j += 1


def scegliEpisodi(url_episodi: list[str]) -> tuple[int, int]:
    """fa scegliere gli ep da guardare all'utente"""
    
    my_print(a.name, cls=True)
    #se contiene solo 1 ep sarà riprodotto automaticamente
    if a.ep == 1:
        return 1, 1

    if lista:
        return a.ep, a.ep

    # faccio decire all'utente il range di ep
    while True:
        if (nome_os == "Android"):
            my_print("Attenzione! Su Android non è ancora possibile specificare un range per lo streaming", color="giallo")
        my_print(f"Specifica un episodio, o per un range usa: ep_iniziale-ep_finale (Episodi: 1-{str(a.ep)})\n>", color="magenta", end=" ")
        n_episodi = input()
        # controllo se l'utente ha inserito un range o un episodio unico (premere invio di default selezione automaticamente tutti gli episodi)
        if "-" not in n_episodi:
            if n_episodi == '':
                ep_iniziale = 1
                ep_finale = a.ep
                break
            else:
                ep_iniziale = int(n_episodi)
                ep_finale = int(n_episodi)
                if (ep_iniziale > a.ep or ep_iniziale < 1):
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
            if (ep_iniziale > ep_finale or ep_finale > a.ep or ep_iniziale < 1):
                my_print("La ricerca non ha prodotto risultati", color="rosso")
            else:
                break

    return ep_iniziale, ep_finale




def downloadPath():
    if (nome_os == "Android"):
        path = f"storage/downloads/{a.name}"
    else:
        path = f"{Path.home()}/Videos/Anime/{a.name}"
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def scaricaEpisodio(url_ep: str, path: str):
    """utilizza la libreria PySmartDL
    per scaricare l'ep e lo salva in una cartella.
    se l'ep è già presente nella cartella non lo riscarica"""

    gia_scaricato = 0
    my_print("Preparo il download...", color="giallo")
    nome_video = url_ep.split('/')[-1]

    # se l'episodio non è ancora stato scaricato lo scarico, altrimenti skippo
    my_print(f"Episodio: {nome_video}", color="blu")
    if not os.path.exists(str(path) + "/" + nome_video):
        SDL = SmartDL(url_ep, path)
        SDL.start()
    else:
        my_print("Episodio già scaricato, skippo...", color="giallo")
        gia_scaricato += 1


def open_Syncplay(url_ep: str):
    """crea un file dove inserisce i link
    degli episodi e avvia syncplay"""

    os.system(f"syncplay  {url_ep} -a syncplay.pl:8999 --language it &>/dev/null")


def OpenPlayer(url_server: str):
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
        player._set_property("keep-open", True)
        player.play(url_server)
        player.wait_for_shutdown()
        player.terminate()


def openDownlodedVideos(path_episodi: list[str]):
    for path_ep in path_episodi:
        nome_video = path_ep.split('/')[-1]
        my_print(f"Riproduco {nome_video}...", color="giallo", cls=True)
        OpenPlayer(path_ep)



def chiediSeAprireDownload(path_video: list[str]):
    while True:
        my_print("Aprire ora il player con gli episodi scaricati? (S/n)\n>", color="magenta", end=" ")
        match input().lower():
            case 's'|"": 
                openDownlodedVideos(path_video)
                break
            case 'n': break
            case  _: my_print("Seleziona una risposta valida", color="rosso")


def openVideos(url_episodi: list[str]):
    for url_ep in url_episodi:
        url_server = trovaUrlServer(url_ep)
        nome_video = url_server.split('/')[-1]
        my_print(f"Riproduco {nome_video}...", color="giallo", cls=True)
        OpenPlayer(url_server)


def main():
    global syncpl
    global download
    global lista
    global a

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
        download = True
    elif args.lista:
        lista = True

    try:
        animes = listaUscite(args.lista) if lista else RicercaAnime()
        
        while True:
            clearScreen()
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

            
            url_episodi = UrlEpisodi(animes[s].url)
            a = animes[s]
            a.ep = len(url_episodi)
            
            if a.ep != 0:
                break

            # se l'anime non ha episodi non può essere selezionato
            my_print("Eh, volevi! L'anime non ha episodi", color="rosso")
            time.sleep(1)

        ep_iniziale, ep_finale = scegliEpisodi(url_episodi)

        # se syncplay è stato scelto allora non chiedo
        # di fare il download ed esco dalla funzione
        if not syncpl and download:
            path_video = []
            path = downloadPath()
            for i in range(ep_iniziale - 1, ep_finale):
                url_ep = trovaUrlServer(url_episodi[i])
                nome_video = url_ep.split('/')[-1]
                scaricaEpisodio(url_ep, path)
                path_video.append(f"{path}/{nome_video}")

            my_print("Tutti i video scaricati correttamente!\nLi puoi trovare nella cartella", color="verde", end=" ")
            if nome_os == "Android":
                my_print("Downloads", color="verde")
            else:
                my_print("Video/Anime", color="verde")
                chiediSeAprireDownload(path_video)
            exit()

        ris_valida = True
        while True:
            if ris_valida:
                openVideos(url_episodi[ep_iniziale-1:ep_finale])
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
            if scelta_menu == 'p' and ep_iniziale < a.ep:
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
                ep_iniziale, ep_finale = scegliEpisodi(url_episodi)
            elif scelta_menu == 'e' or scelta_menu == '':
                exit()
            else:
                clearScreen()
                ris_valida = False

    except KeyboardInterrupt:
        exit()


# controllo il tipo del dispositivo
nome_os = hpcomt.Name()
#args
syncpl = False
download = False
lista = False
# classe
a = Anime()
sito = AnimeWorld()

if __name__ == "__main__":
    main()
