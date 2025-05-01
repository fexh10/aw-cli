import re
from awcli.anime import Anime
from awcli.providers import Provider
from awcli import utilities as ut

class Animeworld(Provider):
    """
    Classe che gestisce il collegamento con Animeworld.
    """
    _url = "https://www.animeworld.so"
    
    def search(self, input: str) -> list[Anime]:
        ut.my_print("Ricerco...", color="giallo")
        url_ricerca = self._url + "/search?keyword=" + input.replace(" ", "+")
        html = getHtml(url_ricerca)
        if re.search(r'<div class="alert alert-danger">', html):
            return []

        animes = list[Anime]()
        # prendo i link degli anime relativi alla ricerca
        for url, name in re.findall(r'<div class="inner">(?:.|\n)+?<a href="([^"]+)"\s+data-jtitle="[^"]+"\s+class="name">([^<]+)', html):
            if nome_os == "Android":
                caratteri_proibiti = '"*/:<>?\|'
                caratteri_rimpiazzo = '”⁎∕꞉‹›︖＼⏐'
                for a, b in zip(caratteri_proibiti, caratteri_rimpiazzo):
                    name = name.replace(a, b)
            animes.append(Anime(unescape(name), self._url+url))
        
        return animes