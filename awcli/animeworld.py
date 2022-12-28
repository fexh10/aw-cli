import requests
from bs4 import BeautifulSoup
from awcli.run import Anime, my_print


class AnimeWorld():
    _url = "https://www.animeworld.tv"
    
    def search(self, input: str) -> list[Anime]:
        # cerco l'anime su animeworld
        my_print("Ricerco...", color="giallo")
        url_ricerca = self._url + "/search?keyword=" + input.replace(" ", "+")
        bs = BeautifulSoup(requests.get(url_ricerca).text, "lxml")

        

        animes = list[Anime]()
        # prendo i link degli anime relativi alla ricerca
        for div in bs.find(class_='film-list').find_all(class_='inner'):
            anime = Anime()
            anime.url = self._url + div.a.get('href')
            
            for a in div.find_all(class_='name'):
                anime.name =a.text

            animes.append(anime)

        return animes
