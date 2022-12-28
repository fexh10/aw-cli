import requests
from bs4 import BeautifulSoup
from awcli.utilities import Anime, my_print

_url = "https://www.animeworld.tv"

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
        anime = Anime()
        anime.url = _url + div.a.get('href')
        
        for a in div.find_all(class_='name'):
            anime.name =a.text

        animes.append(anime)

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
        anime = Anime()
        anime.url = _url + div.a.get('href')
        
        for a in div.find_all(class_='name'):
            anime.name = a.text
        for div in div.find_all(class_='ep'):
            anime.name += " [" + div.text + "]"
        
        animes.append(anime)

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