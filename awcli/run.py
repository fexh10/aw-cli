import os
from bs4 import BeautifulSoup
import requests
import re
import mimetypes
import mpv
import time
from pySmartDL import SmartDL
from pathlib import Path
import hpcomt
import argparse

class Anime:
    name = ""
    ep = 0

def clearScreen():
    os.system('cls' if os.name == 'nt' else 'clear')

def trovaUrlServer(url_ep):
    #creo un obj BS con la pagina dell'ep
    html = requests.get(url_ep).text
    sp = BeautifulSoup(html, "lxml")
    #trovo tutti gli url della pagina
    tutti_url = TrovaUrl(str(sp))
    #variabile temp per capire in che posizione è l'url tra tutti gli url della pagina
    j = 0
    #ciclo for con il numoro totale degli url
    for i in range (0, len(tutti_url)):
        #se l'url è un video e si trova in posizione 1 allora è quello del server
        if(mimetypes.MimeTypes().guess_type(tutti_url[i])[0] == 'video/mp4'):
            if(j==1):
                return tutti_url[i]
            j+=1

def chiediSeAprireDownload(nomi_video):
    while True:
            aprire_ora = input("\033[1;35;40mAprire ora il player con gli episodi scaricati? (S/n)\n> \033[1;37;40m")
            if aprire_ora.lower() == 's' or aprire_ora == "": 
                openDownloadedVideos(nomi_video)
            elif aprire_ora.lower() == 'n':        
                exit()
            else:
                print("\033[1;31;40mSeleziona una risposta valida\033[1;37;40m")

#la funzione utilizza la libreria PySmartDL
#per scaricare gli ep e gli salva in una cartella.
#se l'ep è già presente nella cartella non lo riscarica
def scaricaEpisodi(url_ep):
    gia_scaricato = 0
    print("\033[1;33;40mPreparo il download... \033[1;37;40m")
    if (nome_os == "Android"):
        path = "storage" + "/" + "downloads" + "/" + a.name
    else:
        path = str(Path.home()) + "/Videos/Anime/" + a.name
    if not os.path.exists(path):
        os.makedirs(path)
    nome_video = url_ep.split('/')[-1]
    # se l'episodio non è ancora stato scaricato lo scarico, altrimenti skippo
    if not os.path.exists(str(path) + "/" + nome_video):
        print("\033[1;34;40mEpisodio: " + nome_video + "\033[1;37;40m")
        SDL = SmartDL(url_ep, path)
        SDL.start()
    else:
        print("\033[1;34;40mEpisodio: " + nome_video + "\033[1;37;40m")
        print("\033[1;33;40mEpisodio già scaricato, skippo... \033[1;37;40m")
        gia_scaricato += 1
    return nome_video
        
#la funzione fa scegliere gli ep 
#da guardare all'utente
def scegliEpisodi(syncpl, download, url_episodi):
    # faccio decire all'utente il range di ep, se l'anime contiene solo 1 ep sarà riprodotto automaticamente
    clearScreen()
    print("\033[1;37;40m" + a.name + "\033[1;37;40m ")
    if (a.ep != 1):
        while True:
            if (nome_os == "Android"):
                print(
                    "\033[1;33;40mAttenzione! Su Android non è ancora possibile specificare un range per lo streaming\033[1;37;40m")
            n_episodi = input(
                "\033[1;35;40mSpecifica un episodio, o per un range usa: ep_iniziale-ep_finale (Episodi: 1-" + str(a.ep) + ")\n> " + "\033[1;37;40m")
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
                        print(
                            "\033[1;31;40mLa ricerca non ha prodotto risultati\033[1;37;40m")
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
                    print(
                        "\033[1;31;40mLa ricerca non ha prodotto risultati\033[1;37;40m")
                else:
                    break
    else:
        ep_iniziale = 1
        ep_finale = 1
    
    # se syncplay è stato scelto allora non chiedo 
    #di fare il download ed esco dalla funzione
    if syncpl:
        return ep_iniziale, ep_finale
    elif download:
        nomi_video = []
        for i in range(ep_iniziale - 1, ep_finale):
            url_ep = trovaUrlServer(url_episodi[i])
            nomi_video.append(scaricaEpisodi(url_ep))
        if nome_os == "Android":
            print("\033[1;32;40mTutti i video scaricati correttamente!\nLi puoi trovare nella cartella Downloads\033[1;37;40m")
            exit()
        else:
            print("\033[1;32;40mTutti i video scaricati correttamente!\nLi puoi trovare nella cartella Video, dentro la cartella Anime\033[1;37;40m")
            chiediSeAprireDownload(nomi_video)
    #print("\033[1;33;40mApro il player...\033[1;37;40m")
    return ep_iniziale, ep_finale

#la funzione prende i video scaricati e li apre
def openDownloadedVideos(nomi_video):
    print("\033[1;33;40mApro il player...\033[1;37;40m")
    path = str(Path.home()) + "/Videos/Anime/" + a.name
    for i in range(len(nomi_video)):
        player = mpv.MPV(input_default_bindings=True,
                         input_vo_keyboard=True, osc=True)
        player.play(path + "/" + nomi_video[i])  
        print("\033[1;33;40mRiproduco", nomi_video[i].replace(".mp4", ""), "...\033[1;37;40m")
        # avvio il player
        player.fullscreen = True
        player._set_property("keep-open", True)
        player.wait_for_shutdown()
        player.terminate()
    exit()

#la funzione crea un file dove inserisce i link
#degli episodi e avvia syncplay
def open_Syncplay(url_ep):
    os.system("syncplay  " + url_ep + " -a syncplay.pl:8999 --language it &>/dev/null")

#la funzione prende in input il link
#del video e apre il player per riprodurre il video
def OpenPlayer(url_server, syncpl):
    if syncpl:
        open_Syncplay(url_server)
    elif (nome_os == "Android"):
        # apro il player utilizzando bash e riproduco un video
        #os.system("am start --user 0 -a android.intent.action.VIEW -d \"" +
                      #url_server+"\" -n org.videolan.vlc/org.videolan.vlc.gui.video.VideoPlayerActivity -e \""+a.name+"ep "+str(a.ep)+"\" \"$trackma_title\" > /dev/null 2>&1 &")

        os.system("am start --user 0 -a android.intent.action.VIEW -d \""+url_server+"\" -n is.xyz.mpv/.MPVActivity > /dev/null 2>&1 &")
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

# trova qualsisi url in una stringa
def TrovaUrl(string):
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    url = re.findall(regex, string)
    return [x[0] for x in url]

#scraping per le ultime uscite di anime se AW
def listaUscite(selected):
    url_ricerca = "https://www.animeworld.tv"
    contenuto_html = requests.get(url_ricerca).text
    bs = BeautifulSoup(contenuto_html, "lxml")

    risultati_ricerca = []
    nomi_anime = []
    data_name = "all"

    if selected == "s":
        data_name = "sub"
    elif selected == 'd':
        data_name = "dub"
        
    div = bs.find("div", {"data-name" : data_name})
    for div in div.find_all(class_='inner'):
        temp = ""
        risultati_ricerca.append( "https://www.animeworld.tv" + div.a.get('href'))
        for a in div.find_all(class_='name'):
            temp = a.text
        for div in div.find_all(class_='ep'):
            temp +=  " [" + div.text + "]"
            nomi_anime.append(temp)

    return risultati_ricerca, nomi_anime

# dato in input un nome di un anime inserito dall'utente,
# la funzione restituisce un array con gli url degli anime
# relativi alla ricerca
def RicercaAnime():
    while True:
        clearScreen()
        scelta = input("\033[1;35;40mCerca un anime\n> \033[1;37;40m")
        #esco se metto exit
        if (scelta == "exit"):
            exit()
    
        rimpiazza = scelta.replace(" ", "+")
        # cerco l'anime su animeworld
        url_ricerca = "https://www.animeworld.tv/search?keyword=" + rimpiazza

        print("\033[1;33;40mRicerco...\033[1;37;40m")

        # prendo i link degli anime relativi alla ricerca
        contenuto_html = requests.get(url_ricerca).text
        bs = BeautifulSoup(contenuto_html, "lxml")

        risultati_ricerca = []
        nomi_anime = []
        
        div = bs.find(class_='film-list')
        for div in div.find_all(class_='inner'):
            risultati_ricerca.append( "https://www.animeworld.tv" + div.a.get('href'))
            for a in div.find_all(class_='name'):
                nomi_anime.append(a.text)
        if (len(risultati_ricerca) != 0):
            return risultati_ricerca, nomi_anime
        else:
            print(
                "\033[1;31;40mLa ricerca non ha prodotto risultati\033[1;37;40m")
            time.sleep(1)

# la funzione prende in input l'url dell'anime scelto dall'utente
# e salva in una variabile gli url di tutti gli episodi,
# ricercandoli nell'html della pagina
def UrlEpisodi(url):
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

def openVideos(ep_iniziale, ep_finale, url_episodi, syncpl):
    for i in range(ep_iniziale - 1, ep_finale):
        url_ep = url_episodi[i]
        url_server = trovaUrlServer(url_ep)
        clearScreen()
        print("\033[1;33;40mRiproduco", a.name, "Episodio", i + 1, "...\033[1;37;40m")
        OpenPlayer(url_server, syncpl)
        clearScreen()

def main():
    try:
     #args
        syncpl = False
        download = False
        lista = False
        parser = argparse.ArgumentParser("aw-cli", description="Guarda anime dal terminale e molto altro!")
        if nome_os != "Android":
            parser.add_argument('-s', '--syncplay', action='store_true', dest = 'syncpl', help = 'usa syncplay per guardare un anime insieme ai tuoi amici')  
        parser.add_argument('-d', '--download', action='store_true', dest = 'download', help = 'scarica gli episodi che preferisci')
        parser.add_argument('-l', '--lista',nargs='?', choices=['a', 's', 'd'], dest = 'lista', help = 'lista degli ultimi anime usciti su AnimeWorld. a = all, s = sub, d = dub')
        args = parser.parse_args() 

        if nome_os != "Android":
            if args.syncpl:
                syncpl = True
        if args.download:
            download = True
        elif args.lista:
            lista = True

        if lista:
            risultati_ricerca, nomi_anime = listaUscite(args.lista)
        else:
            risultati_ricerca, nomi_anime = RicercaAnime()
        while True:
            clearScreen()
            # stampo i nomi degli anime
            for i, e in reversed(list(enumerate(nomi_anime))):
                print("\033[1;32;40m", i + 1,
                        "\033[1;37;40m", str(e))

            '''
            for i in range(0, len(nomi_anime)):
                print("\033[1;32;40m", i + 1,
                        "\033[1;37;40m", str(nomi_anime[i]))
            '''
            s = int(input("\033[1;35;40mScegli un anime\n> \033[1;37;40m"))
            #controllo che il numero inserito sia giusto
            while (s < 1 or s > len(nomi_anime)):
                print("\033[1;31;40mSeleziona una risposta valida\033[1;37;40m")
                s = int(input("\033[1;35;40mScegli un anime\n> \033[1;37;40m"))

            url = risultati_ricerca[(s - 1)]
            url_episodi = UrlEpisodi(url)
            a.ep = len(url_episodi)

            # se l'anime non ha episodi non può essere selezionato
            if a.ep == 0:
                print( "\033[1;31;40mEh, volevi! L'anime non ha episodi\033[1;37;40m")  
                time.sleep(1)                       
            else:
                break

        a.name = nomi_anime[(s - 1)]
        # trovo il link del primo url server
        # creo un obj BS con la pagina dell'ep
        html = requests.get(url_episodi[0]).text
        sp = BeautifulSoup(html, "lxml")

        # trovo tutti gli url della pagina
        tutti_url = TrovaUrl(str(sp))

        # variabile temp per capire in che posizione è l'url tra tutti gli url della pagina
        j = 0
        # ciclo for con il numoro totale degli url
        for i in range(0, len(tutti_url)):
            # se l'url è un video e si trova in posizione 1 allora è quello del server
            if (mimetypes.MimeTypes().guess_type(tutti_url[i])[0] == 'video/mp4'):
                if (j == 1):
                    # aggiungo alla varibile sempre e solo l'url server del primo episodio
                    a.url = tutti_url[i]
                    break
                j += 1

        if not lista:
            ep_iniziale, ep_finale = scegliEpisodi(syncpl, download, url_episodi)
            #url_server = a.get_url_range(ep_iniziale, ep_finale)
        
            openVideos(ep_iniziale, ep_finale, url_episodi, syncpl)
                           
        else:
            ep_iniziale = a.ep
            ep_finale = a.ep
            openVideos(ep_iniziale, ep_finale, url_episodi, syncpl)


        ris_valida = False
        prima_volta = True
        while True:
            if ris_valida:
                openVideos(ep_iniziale, ep_finale, url_episodi, syncpl)
            else:
                if prima_volta:
                    prima_volta = False
                else:
                    print("\033[1;31;40mSeleziona una risposta valida\033[1;37;40m")
            ris_valida = True
            # menù che si visualizza dopo aver finito la riproduzione
            scelta_menu = input(
                "\033[1;36;40m(p) prossimo \n" +
                "\033[1;34;40m(r) riguarda \n" + 
                "\033[1;36;40m(a) antecedente\n" + 
                "\033[1;32;40m(s) seleziona\n" + 
                "\033[1;31;40m(e) esci\n" + 
                "\033[1;35;40m> \033[1;37;40m")
            if scelta_menu.lower() == 'p' and ep_iniziale < a.ep:
                ep_iniziale = ep_finale + 1
                ep_finale = ep_iniziale
                continue
            elif scelta_menu.lower() == 'r':
                continue
            elif scelta_menu.lower() == 'a' and ep_iniziale > 1:
                ep_iniziale = ep_finale - 1
                ep_finale = ep_iniziale
                continue
            elif scelta_menu.lower() == 's':
                ep_iniziale, ep_finale = scegliEpisodi(syncpl, download, url_episodi)
            elif scelta_menu.lower() == 'e' or scelta_menu == '':
                exit()
            else:
                clearScreen()
                ris_valida = False

    except KeyboardInterrupt:
        exit()

# controllo il tipo del dispositivo
nome_os = hpcomt.Name()
# classe
a = Anime()                                

if __name__ == "__main__":
    main()
