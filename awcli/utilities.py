import os
import re
import requests
from platform import system
from time import sleep
from bs4 import BeautifulSoup
import awcli.anilist as anilist
from awcli.anime import Anime
   
_url = "https://www.animeworld.so"
# controllo il tipo del dispositivo
nome_os = system()
if nome_os == "Linux":
    if "com.termux" in os.popen("type -p python3").read().strip():
        nome_os = "Android"

def my_print(text: str = "", format: int = 1, color: str = "bianco", bg_color: str = "nero", cls: bool = False, end: str = "\n"):
    """
    Stampa il testo con il formato, colore e lo sfondo specificato.

    Args:
        text (str): il testo da stampare
        format (int, optional): il formato della stampa. Valore predefinito: 1.
        color (str, optional): il colore del testo. Valore predefinito: "bianco".
        bg_color (str, optional): il colore dello sfondo. Valore predefinito: "nero".
        cls (bool, optional): se impostato a True, pulisce lo schermo prima di stampare il testo. Valore predefinito: False.
        end (str, optional): il carattere di fine linea da utilizzare. Valore predefinito: "\n".
    """
    COLORS = {'nero': 0,'rosso': 1,'verde': 2,'giallo': 3,'blu': 4,'magenta': 5,'azzurro': 6,'bianco': 7}
    if cls:
        os.system('cls' if os.name == 'nt' else 'clear')

    print(f"\033[{format};3{COLORS[color]};4{COLORS[bg_color]}m{text}\033[1;37;40m", end=end)

def my_input(text: str, format = lambda i: i, error: str = "Seleziona una risposta valida!", cls = False):
    """
    Funzione personalizzata d'input che restituisce un input formattato sse format(input) != None

    Args:
        text (str): testo da stampare
        format (callable, optional): funzione che formatta l'input se possibile altrimenti restituisce None. Valore predefinito: funzione identità.
        error (str, optional): messaggio di errore in caso di formato errato. Valore predefinito: "Seleziona una risposta valida!".
        cls (bool, optional): se impostato a True esegue la clearscreen dopo 1 secondo. Valore predefinito: False.

    Returns:
        Input formattato dalla funzione format, se fornita. Altrimenti, restituisce l'input immutato.
    """
    while True:
        my_print(f"{text}\n>", end=" ", color="magenta")
        if (i := format(input())) is not None:
            break

        my_print(error, color="rosso")
        if cls:
            sleep(1)
            my_print("",end="", cls=True)
    return i


def getBs(url: str) -> BeautifulSoup:
    """
    Prende l'html della pagina web selezionata.

    Args:
        url (str): indica la pagina web da cui prendere l'html.

    Returns:
        BeautifulSoup: l'html della pagina web selezionata.
    """
    try:
        result = requests.get(url, headers=headers)
    except requests.exceptions.ConnectionError:
        my_print("Errore di connessione", color="rosso")
        exit()
    
    if result.status_code != 200:
        my_print("Errore: pagina non trovata", color="rosso")
        exit()
    
    return BeautifulSoup(result.text, "html.parser")


def search(input: str) -> list[Anime]:
    """
    Ricerca l'anime selezionato su AnimeWorld.

    Args:
        input (str): la stringa di ricerca da effettuare.
        nome_os (str): il nome del sistema operativo in uso.

    Returns:
        list[Anime]: la lista degli anime trovati
    """
    # cerco l'anime su animeworld
    my_print("Ricerco...", color="giallo")
    url_ricerca = _url + "/search?keyword=" + input.replace(" ", "+")
    bs = getBs(url_ricerca)

    animes = list[Anime]()
    # prendo i link degli anime relativi alla ricerca
    for div in bs.find(class_='film-list').find_all(class_='inner'):
        url = _url + div.a.get('href')
        
        for a in div.find_all(class_='name'):
            name =a.text
            if nome_os == "Android":
                caratteri_proibiti = '"*/:<>?\|'
                caratteri_rimpiazzo = '”⁎∕꞉‹›︖＼⏐'
                for a, b in zip(caratteri_proibiti, caratteri_rimpiazzo):
                    name = name.replace(a, b)

        animes.append(Anime(name, url))

    return animes

def latest(filter = "all") -> list[Anime]:
    """
    Restituisce le ultime uscite anime su AnimeWorld.

    Args:
        filter (str, optional): filtra i risultati per versione dubbed o subbed.

    Returns:
        list[Anime]: la lista degli anime trovati
    """

    match filter[0]:
        case 's': data_name = "sub"
        case 'd': data_name = "dub"
        case 't': data_name = "trending"
        case  _ : data_name = "all"

    bs = getBs(_url)
    animes = list[Anime]()

    div = bs.find("div", {"data-name": data_name})
    for div in div.find_all(class_='inner'):
        url = _url + div.a.get('href')
        
        for a in div.find_all(class_='name'):
            name = a.text
            if nome_os == "Android":
                caratteri_proibiti = '"*/:<>?\|'
                caratteri_rimpiazzo = '”⁎∕꞉‹›︖＼⏐'
                for a, b in zip(caratteri_proibiti, caratteri_rimpiazzo):
                    name = name.replace(a, b)
        for div in div.find_all(class_='ep'):
            ep = div.text[3:]
            if ".5" not in ep:
                animes.append(Anime(name, url, int(ep)))
        

    return animes

def download(url_ep: str) -> str:
    """
    Cerca il link di download alternativo nella pagina selezionata.

    Args:
        url_ep (str): indica la pagina dell'episodio

    Returns:
        str: il link di download
    """
    bs = getBs(url_ep)

    links = bs.find(id="download").find_all("a")
    return links[1].get('href')


def get_info_anime(url: str) -> tuple[int, list[str], list[str]]:
    """
    Prende le informazioni dell'anime selezionato.

    Args:
        url (str): indica la pagina dell'anime.

    Returns:
        tuple[int, list[str], list[str]]: l'id di AniList, la lista degli url degli episodi e la lista delle info dell'anime.
    """
    # prendo l'html dalla pagina web di AW
    bs = getBs(url)

    # prendo l'id di anilist
    try:
        id_anilist = int(bs.find(class_='anilist control tip tippy-desktop-only').get('href')[25:])   
    except AttributeError:
        id_anilist = 0 
    # prendo gli url degli episodi
    url_episodi = list[str]()
    for div in bs.find_all(class_='server active'):
        for li in div.find_all(class_="episode"):
            if ".5" in li.a.get('data-num'):
                continue
            temp = _url + (li.a.get('href'))
            url_episodi.append(temp)
            
    # prendo le info dell'anime
    info = list[str]()
    infoDiv = bs.find(class_='info col-md-9')
    for i, div in enumerate(infoDiv.find(class_='row').find_all("dd")):
        match i:
            case 5: info.append(re.sub(r'\s+', ' ', div.text).strip())
            case 9: info.append(div.a.get('href')[-1])
            case _: info.append(div.text.strip())
    
    info.append(re.sub(r'\s+', ' ', infoDiv.find(class_='desc').text).strip())
    
    return id_anilist, url_episodi, info
        

def downloaded_episodes(anime: Anime, path: str) -> None:
        """
        Prende i nomi degli episodi scaricati in base all'anime scelto e
        ne ricava il primo e l'ultimo episodio riproducibili.

        Args:
            path (str): il path dell'anime scelto dall'utente.
        """
        nomi_episodi = os.listdir(path)
        togli = f"{anime.name} Ep. "
        if len(nomi_episodi) != 0:
            temp = nomi_episodi[0].replace(togli, "")
            minimo = int(temp.replace(".mp4", ""))
            massimo = minimo

            for stringa in nomi_episodi:
                stringa = stringa.replace(togli, "")
                stringa = int(stringa.replace(".mp4", ""))
                if stringa < minimo:
                    minimo = stringa
                if stringa > massimo:
                    massimo = stringa
            anime.ep = massimo 
            anime.ep_ini = minimo
        else:
            anime.ep = 0
            anime.ep_ini = 0


def getConfig() -> tuple[bool, str, str]:
    """
    Prende le impostazioni scelte dall'utente
    dal file di configurazione.

    Returns:
        tuple[bool, str, int]: 
        mpv restituisce True se è stato scelto MPV, altrimenti false se è VLC.
        player_path restituisce il path del player predefinito.
        syncplay_path restituisce il path di syncplay.
    """

    config = f"{os.path.dirname(__file__)}/aw.config"

    with open(config, 'r+') as config_file:
        lines = config_file.readlines()

        if len(lines) < 7:
            return None, "", ""

        mpv = True if "mpv" in lines[0].strip() else False
        player_path = lines[0].strip()

        anilist.tokenAnilist = lines[1].strip()
        anilist.ratingAnilist = True if lines[2].strip() == "ratingAnilist: True" else False
        anilist.preferitoAnilist = True if lines[3].strip() == "preferitoAnilist: True" else False
        anilist.dropAnilist = True if lines[4].strip() == "dropAnilist: True" else False
        anilist.user_id = int(lines[5])

        syncplay_path = lines[6].strip()

    return mpv, player_path, syncplay_path


headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'
}