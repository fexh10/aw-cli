import os
import requests
from platform import system
from time import sleep
from bs4 import BeautifulSoup
import re
from awcli.anime import Anime
   
_url = "https://www.animeworld.so"
tokenAnilist = None
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
    bs = BeautifulSoup(requests.get(url_ricerca, headers=headers).text, "lxml")

    animes = list[Anime]()
    # prendo i link degli anime relativi alla ricerca
    for div in bs.find(class_='film-list').find_all(class_='inner'):
        url = _url + div.a.get('href')
        
        for a in div.find_all(class_='name'):
            name =a.text
            if nome_os == "Windows" or nome_os == "Android":
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

    bs = BeautifulSoup(requests.get(_url, headers=headers).text, "lxml")
    animes = list[Anime]()

    div = bs.find("div", {"data-name": data_name})
    for div in div.find_all(class_='inner'):
        url = _url + div.a.get('href')
        
        for a in div.find_all(class_='name'):
            name = a.text
            if nome_os == "Windows" or nome_os == "Android":
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
    bs = BeautifulSoup(requests.get(url_ep, headers=headers).text, "lxml")

    links = bs.find(id="download").find_all("a")
    return links[1].get('href')

def episodes(url_ep: str) -> tuple[str, int, int, str]:
    """
    Cerca i link degli episodi dell'anime nella pagina selezionata e 
    controlla se è ancora in corso.

    Args:
        url_ep (str): indica la pagina dell'episodio.

    Returns:
        tuple[str, int, int, str]: la lista con gli URL dei vari episodi trovati, 
        lo stato dell'anime, l'id di AniList se si ha effettuato l'accesso
        e il numero reale degli episodi totali dell'anime.
    """

    # prendo l'html dalla pagina web di AW
    bs = BeautifulSoup(requests.get(url_ep, headers=headers).text, "lxml")

    url_episodi = list[str]()
    # cerco gli url di tutti gli episodi
    for div in bs.find_all(class_='server active'):
        for li in div.find_all(class_="episode"):
            if ".5" in li.a.get('data-num'):
                continue
            temp = _url + (li.a.get('href'))
            url_episodi.append(temp)
    #cerco lo stato dell'anime. 1 se è finito, altrimenti 0
    status = 1
    dl = bs.find_all(class_='meta col-sm-6')
    for a in dl[1].find_all("a"):
        if "filter?status=0"in a.get('href'):
            status = 0
            break
    #cerco il numero reale di episodi totali dell'anime
    ep_totali = bs.find_all("dd")[12].string if status == 0 else len(url_episodi) 
    #cerco l'id di anilist
    id_anilist = 0
    try:
        if tokenAnilist != 'tokenAnilist: False':
            id_anilist = bs.find(class_='anilist control tip tippy-desktop-only').get('href').replace("https://anilist.co/anime/", "")
    except AttributeError:
        pass

    return url_episodi, status, id_anilist, ep_totali


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


def getAnimeInfo(anime: Anime) -> str:
    """
    Prende le informazioni e la trama relative all'anime selezionato.

    Returns:
        str: la scelta dell'utente nel menu.
    """

    bs = BeautifulSoup(requests.get(anime.url, headers=headers).text, "lxml")
    row = bs.find(class_='info col-md-9').find(class_='row')
    my_print(anime.name, cls=True)
    
    dt = row.find_all("dt")
    dd = row.find_all("dd")
    trama = bs.find(class_='desc')

    #stampo dl e dt
    for i in range(len(dt)):
            if i != 6:
                my_print(dt[i].text.strip(), end=" ", color="azzurro")
            else:
                my_print(dt[i].text.strip().replace(":", " medio: "), end=" ", color="azzurro")
            if i != 5:
                my_print(dd[i].text.strip(), format=0)
            else:
                my_print(re.sub("\s\s+" , " ", dd[i].text.strip()), format=0)
    #stampo la trama
    my_print("Trama:", color="azzurro", end=" ")
    my_print(trama.text, format=0)
    #stampo piccolo menu
    def check_string(s: str):
        s.lower()
        if s == "g" or s == 'i' or s == "":
            return s


    my_print("\n(g) guardare", color='verde')
    my_print("(i) indietro", color='magenta', end="")
    return my_input("", check_string)

def anilistApi(id_anilist: int, ep: int, voto: float, status_list: str, preferiti: bool) -> None:
    """
    Collegamento alle API di AniList per aggiornare
    automaticamente gli anime.

    Args:
        id_anilist (int): l'id dell'anime su AniList.
        ep (int): il numero dell'episodio visualizzato.
        voto (float): il voto dell'anime.
        status_list (str): lo stato dell'anime per l'utente. Se è in corso verrà impostato su "CURRENT", se completato su "COMPLETED".
        preferiti (bool) : True se l'utente ha scelto di mettere l'anime tra i preferiti, altrimenti False.
    """

    #query in base alla scelta del preferito
    if not preferiti:
        query = """
        mutation ($idAnime: Int, $status: MediaListStatus, $episodio : Int, $score: Float) {
            SaveMediaListEntry (mediaId: $idAnime, status: $status, progress : $episodio, score: $score) {
                status
                progress
                score
            }
        }
        """
    else:
        query = """
            mutation ($idAnime: Int, $status: MediaListStatus, $episodio : Int, $score: Float) {
                SaveMediaListEntry (mediaId: $idAnime, status: $status, progress : $episodio, score: $score) {
                    status
                    progress
                    score
                },
                ToggleFavourite(animeId:$idAnime){
                    anime {
                        nodes {
                            id
                        }
                    }
                }
            }
            """

    var = {
        "idAnime" : id_anilist,
        "status" : status_list,
        "episodio" : ep,
    }
    if voto != 0:
        var["score"] = voto
    header_anilist = {'Authorization': 'Bearer ' + tokenAnilist, 'Content-Type': 'application/json', 'Accept': 'application/json'}
    requests.post('https://graphql.anilist.co',headers=header_anilist,json={'query' : query, 'variables' : var}) 

def getAnilistUserId(tokenAnilist: str) -> int: 
    """
    Collegamento alle API di AniList per trovare
    l'id dell'utente.

    Args:
        tokenAnilist: il token AniList dell'utente.

    Returns:
        int: l'id dell'utente.
    """

    query = """
        query {
            Viewer {
                id
            }
        }
    """

    header_anilist = {'Authorization': 'Bearer ' + tokenAnilist, 'Content-Type': 'application/json', 'Accept': 'application/json'}
    risposta = requests.post('https://graphql.anilist.co',headers=header_anilist,json={'query' : query}) 
    user_id = int(risposta.json()["data"]["Viewer"]["id"])

    return user_id

def getConfig() -> tuple[bool, str, bool, bool, int, str]:
    """
    Prende le impostazioni scelte dall'utente
    dal file di configurazione.

    Returns:
        tuple[bool, str, bool, bool, int]: 
        mpv restituisce True se è stato scelto mpv, altrimenti false se è VLC.
        player_path restituisce il path del player predefinito.
        ratingAnilist restituisce True  se l'utente ha scelto di votare gli anime, altrimenti False. preferitoAnilist ritorna
        preferitoAnilist restituisce True se l'utente ha scelto di chiedere se l'anime deve essere aggiunto tra i preferiti,
        altrimenti False.
        user_id restituisce l'id dell'utente. 
        syncplay_path restituisce il path di syncplay.
    """

    global tokenAnilist
    config = f"{os.path.dirname(__file__)}/aw.config"

    with open(config, 'r+') as config_file:
        lines = config_file.readlines()

        mpv = True if "mpv" in lines[0].strip() else False
        player_path = lines[0].strip()

        tokenAnilist = lines[1].strip()
        ratingAnilist = True if lines[2].strip() == "ratingAnilist: True" else False
        preferitoAnilist = True if lines[3].strip() == "preferitoAnilist: True" else False
        if len(lines) == 4 and ratingAnilist == False:
            user_id = 0
        elif len(lines) == 4 and ratingAnilist == True:
            user_id = getAnilistUserId()
            config_file.write(f"{user_id}")
        else:
            user_id = lines[4]
        if len(lines) == 5:
            syncplay_path = None
        else:
            syncplay_path = lines[5]

    return mpv, player_path, ratingAnilist, preferitoAnilist, user_id, syncplay_path

def getAnimePrivateRating(user_id: int, id_anime: int) -> str:
    """
    Collegamento alle API di AniList per trovare
    il voto dato all'anime dall'utente.

    Args:
        user_id (int): l'id dell'utente su AniList.
        id_anime (int): l'id dell'anime su Anilist.

    Returns:
        str: il voto dell'utente sotto forma di stringa.
    """

    query = """
    query ($idAnime: Int, $userId: Int) {
        MediaList(userId: $userId, mediaId: $idAnime) {
            score
        }
    }
    """
    var = {
    "idAnime": id_anime,
    "userId": user_id
}

    header_anilist = {'Authorization': 'Bearer ' + tokenAnilist, 'Content-Type': 'application/json', 'Accept': 'application/json'}
    risposta = requests.post('https://graphql.anilist.co',headers=header_anilist,json={'query' : query, 'variables' : var}) 
    voto = str(risposta.json()["data"]["MediaList"]["score"])
    if voto == "0":
        voto = "n.d."
    return voto

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'
}