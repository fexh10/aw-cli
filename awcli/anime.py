import awcli.utilities as utilities

class Anime:
    """
    Classe che rappresenta un anime.

    Attributes:
        name (str): il nome dell'anime.
        url (str): l'URL della pagina dell'anime su AnimeWorld.  
        ep (int, optional):
        ep_totali (str, optional): il numero reale di episodi totali dell'anime.
    """ 

    def __init__(self, name, url, ep=0, ep_totali="") -> None:
        self.name = name
        self.url = url
        self.ep_corrente = ep-1
        self.progress = {}
        self.ep = ep
        self.ep_totali = ep_totali
        self.ep_ini = 1
        
    def load_info(self) -> None:
        """
        Cerca le informazioni dell'anime e le salva.
        """
        try:
            res = utilities.get_info_anime(self.url)
        except IndexError:
            utilities.my_print("Il link è stato cambiato", color="rosso", end="\n")
            self.url = utilities.search(self.name)[0].url
            res = utilities.get_info_anime(self.url)
            
        self.id_anilist, self.url_episodi, infos = res
        self.ep = len(self.url_episodi)
        self.category = infos[0]
        self.audio = infos[1]
        self.release_date = infos[2]
        self.season = infos[3]
        self.studios = infos[4]
        self.genres = infos[5]
        self.vote = infos[6]
        self.ep_len = infos[7]
        self.ep_totali = infos[8]
        self.status = int(infos[9])
        self.views = infos[10]
        self.plot = infos[11]
        
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
            return utilities.download(self.url_episodi[ep])
        
    def ep_name(self, ep: int) -> str:
        """
        Restituisce il nome dell'episodio specificato.

        Args:
            ep (int): il numero dell'episodio.

        Returns:
            str: il nome dell'episodio.
        """
        return f"{self.name} Ep. {ep}"
    
    def print_info(self):
        """
        Stampa le informazioni dell'anime.
        """
        utilities.my_print(self.name, cls=True)
        utilities.my_print("Categoria: ", end="", color="azzurro")
        utilities.my_print(self.category, format=0)
        utilities.my_print("Audio: ", end="", color="azzurro")
        utilities.my_print(self.audio, format=0)
        utilities.my_print("Data di uscita: ", end="", color="azzurro")
        utilities.my_print(self.release_date, format=0)
        utilities.my_print("Stagione: ", end="", color="azzurro")
        utilities.my_print(self.season, format=0)
        utilities.my_print("Studios: ", end="", color="azzurro")
        utilities.my_print(self.studios, format=0)
        utilities.my_print("Generi: ", end="", color="azzurro")
        utilities.my_print(self.genres, format=0)
        utilities.my_print("Voto medio: ", end="", color="azzurro")
        utilities.my_print(self.vote, format=0)
        utilities.my_print("Durata: ", end="", color="azzurro")
        utilities.my_print(self.ep_len, format=0)
        utilities.my_print("Episodi: ", end="", color="azzurro")
        utilities.my_print(self.ep_totali, format=0)
        utilities.my_print("Stato: ", end="", color="azzurro")
        match self.status:
            case 0:
                utilities.my_print("Finito", format=0)
            case 1:
                utilities.my_print("In corso", format=0)
            case 2:
                utilities.my_print("Non rilasciato", format=0)
        utilities.my_print("Visualizzazioni: ", end="", color="azzurro")
        utilities.my_print(self.views, format=0)
        utilities.my_print("Trama: ", end="", color="azzurro")
        utilities.my_print(self.plot, end="\n\n", format=0)
        
 