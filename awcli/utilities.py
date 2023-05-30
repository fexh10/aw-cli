import os
import requests
from time import sleep
from bs4 import BeautifulSoup
import re

class Anime:
    """
    Classe che rappresenta un anime.

    Attributes:
        name (str): il nome dell'anime.
        url (str): l'URL della pagina dell'anime su AnimeWorld.
        ep (int): il numero di episodi dell'anime.
        ep_ini (int): il numero dell'episodio di inizio. Valore predefinito 1
    """ 

    def __init__(self, name, url, ep=0) -> None:
        self.name = name
        self.url = url
        self.ep = ep

    def load_episodes(self, tokenAnilist) -> None:
        """
        Cerca gli URL degli episodi dell'anime e salva il numero di episodi trovati.
        """
        self.url_episodi, self.status, self.id_anilist = episodes(self.url, tokenAnilist)
        self.ep = len(self.url_episodi)
        self.ep_ini = 1

    def get_episodio(self, ep: int) -> str:
        """
        Restituisce il link dell'episodio specificato.

        Args:
            ep (int): il numero dell'episodio.

        Returns:
            str: il link dell'episodio.
        """

        ep -= 1
        if ep in range(self.ep):
            return download(self.url_episodi[ep])
        
    def ep_name(self, ep: int) -> str:
        """
        Restituisce il nome dell'episodio specificato.

        Args:
            ep (int): il numero dell'episodio.

        Returns:
            str: il nome dell'episodio.
        """
        return f"{self.name} Ep. {ep}"

    def downloaded_episodes(self, path: str) -> None:
        """
        Prende i nomi degli episodi scaricati in base all'anime scelto e
        ne ricava il primo e l'ultimo episodio riproducibili.

        Args:
            path (str): il path dell'anime scelto dall'utente.
        """
        nomi_episodi = os.listdir(path)
        togli = f"{self.name} Ep. "
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
            self.ep = massimo 
            self.ep_ini = minimo
        else:
            self.ep = 0
            self.ep_ini = 0

    def getAnimeInfo(self) -> str:
        """
        Prende le informazioni e la trama relative all'anime selezionato.

        Returns:
            str: la scelta dell'utente nel menu.
        """

        bs = BeautifulSoup(requests.get(self.url, headers=headers).text, "lxml")
        row = bs.find(class_='info col-md-9').find(class_='row')
        my_print(self.name, cls=True)
        
        dt = row.find_all("dt")
        dd = row.find_all("dd")
        trama = bs.find(class_='desc')
        return printAnimeInfo(dt, dd, trama)
    
_url = "https://www.animeworld.tv"

def my_print(text: str, format: int = 1, color: str = "bianco", bg_color: str = "nero", cls: bool = False, end: str = "\n"):
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
        input (str): la stringa di ricerca da effettuare

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
        case  _ : data_name = "all"

    bs = BeautifulSoup(requests.get(_url, headers=headers).text, "lxml")
    animes = list[Anime]()

    div = bs.find("div", {"data-name": data_name})
    for div in div.find_all(class_='inner'):
        url = _url + div.a.get('href')
        
        for a in div.find_all(class_='name'):
            name = a.text
        for div in div.find_all(class_='ep'):
            ep = int(float(div.text[3:]))
        animes.append(Anime(name, url, ep))
        

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

def episodes(url_ep: str, tokenAnilist: str) -> tuple[str, int, int]:
    """
    Cerca i link degli episodi dell'anime nella pagina selezionata e 
    controlla se è ancora in corso.

    Args:
        url_ep (str): indica la pagina dell'episodio.
        tokenAnilist (str): il token di accesso ad AniList.

    Returns:
        tuple[str, int, int]: la lista con gli URL dei vari episodi trovati, 
        lo stato dell'anime e l'id di AniList se si ha effettuato l'accesso.
    """

    # prendo l'html dalla pagina web di AW
    bs = BeautifulSoup(requests.get(url_ep, headers=headers).text, "lxml")

    url_episodi = list[str]()
    # cerco gli url di tutti gli episodi
    for div in bs.find_all(class_='server active'):
        for li in div.find_all(class_="episode"):
            if ".5" in li.a.get('data-num'):
                continue
            temp = "https://www.animeworld.tv" + (li.a.get('href'))
            url_episodi.append(temp)
    #cerco lo stato dell'anime. 1 se è finito, altrimenti 0
    status = 1
    dl = bs.find_all(class_='meta col-sm-6')
    for a in dl[1].find_all("a"):
        if "filter?status=0"in a.get('href'):
            status = 0
            break
    #cerco l'id di anilist
    id_anilist = 0
    try:
        if tokenAnilist != 'tokenAnilist: False':
            id_anilist = bs.find(class_='anilist control tip tippy-desktop-only').get('href').replace("https://anilist.co/anime/", "")
    except AttributeError:
        pass

    return url_episodi, status, id_anilist

def printAnimeInfo(dt: list, dd: list, trama: str) -> str:
    """
    Stampa a schermo le informazioni
    e la trama relative all'anime selezioanto.
    Chiede all'utente se guardare l'anime oppure tornare indietro.

    Args:
        dt (list): i campi "dt" della pagina che contengono le informazioni.
        dd (list): i campi "dd" della pagina che contengono le informazioni.
        trama (str): la trama dell'anime.

    Returns:
        str: la scelta dell'utente nel menu.
    """

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

def anilistApi(tokenAnilist: str, id_anilist: int, ep: int, voto: float, status_list: str, preferiti: bool):
    """
    Collegamento alle API di AniList per aggiornare
    automaticamente gli anime.

    Args:
        tokenAnilist (str): il token di accesso ad AniList.
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

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'
}