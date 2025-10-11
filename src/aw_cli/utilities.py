import os
import toml
from time import sleep
from collections import defaultdict

configData = defaultdict(dict)

# controllo il tipo del dispositivo
def get_os() -> str:
    out = os.popen("uname -a").read().strip().split()
    nome_os = out[0]
    if nome_os == "Linux":
        if "Android" == out[-1]:
            nome_os = "Android"
        elif "WSL" in out[2]:
            nome_os = "WSL"
    return nome_os

nome_os = get_os()


def my_print(text: str = "", format: int = 1, color: str = "bianco", bg_color: str = "nero", cls: bool = False, end: str = "\n"):
    """
    Stampa il testo con il formato, colore e lo sfondo specificato.

    Args:
        text (str): il testo da stampare
        format (int, optional): il formato della stampa. Valore predefinito: 1.
        color (str, optional): il colore del testo. Valore predefinito: "bianco".
        bg_color (str, optional): il colore dello sfondo. Valore predefinito: "nero".
        cls (bool, optional): se impostato a True, pulisce lo schermo prima di stampare il testo. Valore predefinito: False.
        end (str, optional): il carattere di fine linea da utilizzare. Valore predefinito: "\\n".
    """
    COLORS = {'nero': 0,'rosso': 1,'verde': 2,'giallo': 3,'blu': 4,'magenta': 5,'azzurro': 6,'bianco': 7, "ciano": 8, "ciano_bg": 110}
    if cls:
        os.system('clear')
    if bg_color == "ciano_bg":
        print(f"\033[{format};3{COLORS[color]};5;{COLORS[bg_color]}m{text}\033[1;37;40m", end=end)
    else:
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
        my_print(f"{text}:", end=" ", color="ciano", bg_color="ciano_bg")
        if (i := format(input())) is not None:
            break

        my_print(error, color="rosso")
        if cls:
            sleep(1)
            my_print("",end="", cls=True)
    return i
                

def sanitize_filename(filename: str) -> str:
    """
    Sanitizza il nome del file rimuovendo i caratteri non validi.

    Args:
        filename (str): il nome del file da sanitizzare.

    Returns:
        str: il nome del file sanitizzato.
    """
    if nome_os != "Android":
        return filename
    
    forbidden_char = '"*/:<>?\|'
    replace_char = '”⁎∕꞉‹›︖＼⏐'
    for a, b in zip(forbidden_char, replace_char):
        filename = filename.replace(a, b)
    return filename

def getConfig() -> None:
    """
    Prende le impostazioni scelte dall'utente
    dal file di configurazione.

    Returns:
        None
    """
    global configData
    
    configPath = f"{os.path.dirname(__file__)}/config.toml"
    
    with open(configPath, 'r') as f:
        configData = toml.load(f)
    
    if nome_os == "WSL": 
        configData["player"]["path"] = f'''"$(wslpath '{configData["player"]["path"]}')"'''
        if "syncplay" in configData:
            configData["syncplay"]["path"] = f"/mnt/c/Windows/System32/cmd.exe /C '{configData["syncplay"]["path"]}'"
    
    if "specials" not in configData["general"]:
        configData["general"]["specials"] = False
