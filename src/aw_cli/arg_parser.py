import sys
import argparse
from .core.env import env
from importlib.metadata import version
from .update import update

class UpdateAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        update(str(values) if values else "")
        parser.exit()

# Parser principale
parser = argparse.ArgumentParser(
    "aw-cli",
    description="Guarda anime dal terminale e molto altro!",
    add_help=True
)

# Parent parser con le opzioni comuni ereditabili dai subcomandi
parent_parser = argparse.ArgumentParser(add_help=False)

parent_parser.add_argument(
    '-i',
    '--info',
    action='store_true',
    dest='info',
    help='visualizza le informazioni e la trama di un anime'
)

parent_parser.add_argument(
    '-d',
    '--download',
    action='store_true',
    dest='download',
    help='scarica gli episodi che preferisci'
)

parent_parser.add_argument(
    '-p',
    '--privato',
    action='store_true',
    dest='private',
    help='guarda un episodio senza che si aggiorni la cronologia o AniList'
)

if env.supports_syncplay:
    parent_parser.add_argument(
        '-s',
        '--syncplay',
        action='store_true',
        dest='syncpl',
        help='usa syncplay per guardare un anime insieme ai tuoi amici'
    )

# Opzioni generali del parser principale (non ereditate)
parser.add_argument(
    '-v',
    '--versione',
    action='version',
    version=version("aw-cli"),
    help="stampa la versione del programma"
)

parser.add_argument(
    '-u',
    '--update',
    nargs='?',
    action=UpdateAction,
    type=str,
    help='aggiorna il programma',
)

parser.add_argument(
    '-a',
    '--configurazione',
    action='store_true',
    dest='start_config',
    help='avvia il menu di configurazione'
)

# Configurazione dei Subcomandi
subparsers = parser.add_subparsers(dest='command', help='Comandi disponibili')

# Default/Fallback action per il parser principale se nessun comando viene specificato
parser.set_defaults(action='search')

# Comando cerca
parser_search = subparsers.add_parser(
    'cerca',
    aliases=['s', 'search'],
    parents=[parent_parser],
    help='Cerca un anime online (default)'
)
parser_search.set_defaults(action='search')

# Comando cronologia
parser_hist = subparsers.add_parser(
    'cronologia',
    aliases=['c', 'history'],
    parents=[parent_parser],
    help='Visualizza la cronologia degli anime'
)
parser_hist.add_argument(
    '-r',
    '--rimuovi',
    action='store_true',
    dest='remove',
    help='Rimuovi un anime dalla cronologia'
)
parser_hist.set_defaults(action='history')

# Comando lista
parser_latest = subparsers.add_parser(
    'lista',
    aliases=['l', 'latest'],
    parents=[parent_parser],
    help='Visualizza gli ultimi anime rilasciati'
)
parser_latest.add_argument(
    'filter',
    nargs='?',
    choices=['a', 's', 'd', 't'],
    default='a',
    help="Filtro per ultime release: a = all, s = sub, d = dub, t = tendenze. Default 'a'"
)
parser_latest.set_defaults(action='latest')

# Comando offline
parser_offline = subparsers.add_parser(
    'offline',
    aliases=['o'],
    parents=[parent_parser],
    help='Apri gli episodi scaricati precedentemente offline'
)
parser_offline.set_defaults(action='offline')

args = parser.parse_args()
