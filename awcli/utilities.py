import os
import requests
from bs4 import BeautifulSoup


class Anime:
    def __init__(self, name, url) -> None:
        self.name = name
        self.url = url

    def __str__(self) -> str:
        return f"name: {self.name}, url: {self.url},  ep: {self.ep}"

    def setUrlEpisodi(self):
        self.url_episodi = episodes(self.url)
        self.ep = len(self.url_episodi)

    def getEpisodio(self, ep: int) -> str:
        ep -= 1
        if ep in range(self.ep):
            return download(self.url_episodi[ep])


_url = "https://www.animeworld.tv"

def my_print(text: str, format=1, color="bianco", bg_color="nero", cls=False, end="\n"):
    COLORS = {'nero': 0,'rosso': 1,'verde': 2,'giallo': 3,'blu': 4,'magenta': 5,'azzurro': 6,'bianco': 7}
    if cls:
        os.system('cls' if os.name == 'nt' else 'clear')

    print(f"\033[{format};3{COLORS[color]};4{COLORS[bg_color]}m{text}\033[1;37;40m", end=end)

def search(input: str) -> list[Anime]:
    """Ricerca l'anime selezionato su AnimeWorld
    :return: la lista degli anime trovati"""

    # cerco l'anime su animeworld
    my_print("Ricerco...", color="giallo")
    url_ricerca = _url + "/search?keyword=" + input.replace(" ", "+")
    bs = BeautifulSoup(requests.get(url_ricerca).text, "lxml")

    animes = list[Anime]()
    # prendo i link degli anime relativi alla ricerca
    for div in bs.find(class_='film-list').find_all(class_='inner'):
        url = _url + div.a.get('href')
        
        for a in div.find_all(class_='name'):
            name =a.text

        animes.append(Anime(name, url))

    return animes

def latest(filter = "a") -> list[Anime]:
    """Ultime uscite anime su AnimeWorld
    :param filter: può essere d, s che indicano rispettivamente dub, sub
    :return: la lista degli anime trovati"""

    bs = BeautifulSoup(requests.get(_url).text, "lxml")

    match filter:
        case 's': data_name = "sub"
        case 'd': data_name = "dub"
        case  _ : data_name = "all"
    
    animes = list[Anime]()

    div = bs.find("div", {"data-name": data_name})
    for div in div.find_all(class_='inner'):
        url = _url + div.a.get('href')
        
        for a in div.find_all(class_='name'):
            name = a.text
        for div in div.find_all(class_='ep'):
            name += " [" + div.text + "]"
        
        animes.append(Anime(name, url))

    return animes

def download(url_ep: str):
    """Cerca il link di download alternativo nella pagina selezionata
    :param url_ep: indica la pagina dell'episodio
    :return: il link di download"""
    bs = BeautifulSoup(requests.get(url_ep).text, "lxml")

    links = bs.find(id="download").find_all("a")
    return links[1].get('href')

def episodes(url_ep: str) -> list[str]:
    """Cerca i link degli episodi dell'annime alla pagina selezionata
    :param url_ep: indica la pagina dell'episodio
    :return: la lista con url dei vari episodi trovati"""

    # prendo l'html dalla pagina web di AW
    bs = BeautifulSoup(requests.get(url_ep).text, "lxml")

    url_episodi = list[str]()
    # cerco gli url di tutti gli episodi
    for div in bs.find_all(class_='server active'):
        for li in div.find_all(class_="episode"):
            temp = "https://www.animeworld.tv" + (li.a.get('href'))
            url_episodi.append(temp)
    return url_episodi