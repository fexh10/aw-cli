import os
from re import findall


class Anime:
    name = ""
    url = ""
    ep = 0


    def __str__(self) -> str:
        return f"name: {self.name}, url: {self.url},  ep: {self.ep}"


def clearScreen():
    os.system('cls' if os.name == 'nt' else 'clear')
    pass


def my_print(text: str, format=1, color="bianco", bg_color="nero", cls=False, end="\n"):
    COLORS = {'nero': 0,'rosso': 1,'verde': 2,'giallo': 3,'blu': 4,'magenta': 5,'azzurro': 6,'bianco': 7}
    if cls:
        clearScreen()

    print(f"\033[{format};3{COLORS[color]};4{COLORS[bg_color]}m{text}\033[1;37;40m", end=end)



def TrovaUrl(string: str) -> list[str]:
    """trova qualsisi url in una stringa"""

    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    url = findall(regex, string)
    return [x[0] for x in url]
