import os


class Anime:
    name = ""
    url = ""
    ep = 0
    url_episodi = []

    def __str__(self) -> str:
        return f"name: {self.name}, url: {self.url},  ep: {self.ep}"

    def getEpisodio(self, ep: int) -> str:
        ep -= 1
        if ep in range(len(self.url_episodi)):
            return "ciao"


def clearScreen():
    os.system('cls' if os.name == 'nt' else 'clear')
    pass


def my_print(text: str, format=1, color="bianco", bg_color="nero", cls=False, end="\n"):
    COLORS = {'nero': 0,'rosso': 1,'verde': 2,'giallo': 3,'blu': 4,'magenta': 5,'azzurro': 6,'bianco': 7}
    if cls:
        clearScreen()

    print(f"\033[{format};3{COLORS[color]};4{COLORS[bg_color]}m{text}\033[1;37;40m", end=end)
