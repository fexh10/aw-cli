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
        self.ep_corrente = ep
        self.ep = ep
        self.ep_totali = ep_totali
        self.ep_ini = 1

    def load_episodes(self) -> None:
        """
        Cerca gli URL degli episodi dell'anime e salva il numero di episodi trovati
        """

        try:
            res = utilities.episodes(self.url)
        except IndexError:
            utilities.my_print("Il link è stato cambiato", color="rosso", end="\n")
            self.url = utilities.search(self.name)[0].url
            res = utilities.episodes(self.url)
            
        self.url_episodi, self.status, self.id_anilist, self.ep_totali = res
        self.ep = len(self.url_episodi)

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
 