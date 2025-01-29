import sys
import argparse
from awcli.version import versione
from awcli.utilities import nome_os 

# args
downl = False
lista = False
offline = False
cronologia = False
info = False
privato = False
update = False

# args
parser = argparse.ArgumentParser(
    "aw-cli",
    description="Guarda anime dal terminale e molto altro!",
    add_help=False
)

info_group = parser.add_argument_group("Informazioni")
options_group = parser.add_argument_group("Opzioni")
config_group = parser.add_argument_group("Configurazione")

info_group.add_argument(
    '-h',
    '--help',
    action='help',
    help="mostra questo messaggio"
)

info_group.add_argument(
    '-v',
    '--versione',
    action='version',
    version=versione, help="stampa la versione del programma"
)

options_group.add_argument(
    '-c',
    '--cronologia',
    nargs='?',
    choices=['r'], dest='cronologia',
    help='continua a guardare un anime dalla cronologia. \'r\' per rimuovere un anime (opzionale)'
)

options_group.add_argument(
    '-l',
    '--lista',
    nargs='?',
    choices=['a', 's', 'd', 't'],
    dest='lista',
    help="lista degli ultimi anime usciti su AnimeWorld. a = all, s = sub, d = dub, t = tendenze. Default 'a'"
)

options_group.add_argument(
    '-i',
    '--info',
    action='store_true',
    dest='info',
    help='visualizza le informazioni e la trama di un anime'
)

options_group.add_argument(
    '-d',
    '--download',
    action='store_true',
    dest='download', help='scarica gli episodi che preferisci'
)

options_group.add_argument(
    '-o',
    '--offline',
    action='store_true',
    dest='offline',
    help='apri gli episodi scaricati precedentemente direttamente dal terminale'
)

options_group.add_argument(
    '-p',
    '--privato',
    action='store_true',
    dest='privato',
    help="guarda un episodio senza che si aggiorni la cronologia o AniList"
)

options_group.add_argument(
    '-u',
    '--update',
    nargs='?',
    dest='update',
    help='aggiorna il programma'
)

config_group.add_argument(
    '-a',
    '--configurazione',
    action='store_true',
    dest='avvia_config',
    help='avvia il menu di configurazione'
)

args = parser.parse_args()

if args.offline:
    offline = True
    cronologia = True
elif args.cronologia == 'r':
        cronologia = True
elif args.update or '-u' in sys.argv:
    update = True
    if len(sys.argv) == 3:
        args.update = sys.argv[2]
else: 
    if args.info:
        info = True
    if args.download:
        downl = True
    if args.lista or '-l' in sys.argv:
        if args.lista == None:
            args.lista = 'a'
        lista = True
    if args.privato:
        privato = True
    if '-c' in sys.argv:
        cronologia = True
    