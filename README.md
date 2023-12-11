# aw-cli
<h3 align="center">

Guarda anime dal terminale e molto altro!<br /> Gli anime vengono presi da <a href="https://www.animeworld.tv/">AnimeWorld</a>

</h3>

## Anteprima
https://user-images.githubusercontent.com/90156014/210212814-e73ba7af-ce12-43ad-95ff-dcd85b39a45c.mp4

## Indice

- [aw-cli](#aw-cli)
  - [Anteprima](#anteprima)
  - [Indice](#indice)
  - [Installazione](#installazione)
  - [Disinstallazione](#disinstallazione)
  - [Utilizzo](#utilizzo)
  - [Crediti](#crediti)


## Installazione

Lo script funziona sia con [MPV](https://mpv.io/installation/) che con [VLC](https://www.videolan.org/vlc/index.it.html). <br /> 

È possibile installare aw-cli da pip:
```
python3 -m pip install aw-cli --upgrade
```
O se si preferisce da sorgente (potrebbe essere più aggiornato):
```
python3 -m pip install git+https://github.com/fexh10/aw-cli.git
```
## Disinstallazione 

```
python3 -m pip uninstall aw-cli
```

## Utilizzo
```
usage: aw-cli [-h] [-v] [-c [{r}]] [-l [{a,s,d,t}]] [-i] [-s] [-d] [-o] [-p] [-a]

Guarda anime dal terminale e molto altro!

Informazioni:
  -h, --help            mostra questo messaggio
  -v, --versione        stampa la versione del programma

Opzioni:
  -c [{r}], --cronologia [{r}]
                        continua a guardare un anime dalla cronologia. 'r' per rimuovere un anime (opzionale)
  -l [{a,s,d,t}], --lista [{a,s,d,t}]
                        lista degli ultimi anime usciti su AnimeWorld. a = all, s = sub, d = dub, t = tendenze. Default 'a'
  -i, --info            visualizza le informazioni e la trama di un anime
  -s, --syncplay        usa syncplay per guardare un anime insieme ai tuoi amici
  -d, --download        scarica gli episodi che preferisci
  -o, --offline         apri gli episodi scaricati precedentemente direttamente dal terminale
  -p, --privato         guarda un episodio senza che si aggiorni la cronologia o AniList

Configurazione:
  -a, --configurazione  avvia il menu di configurazione                                                       
```

## Crediti
Progetto ispirato a <a href="https://github.com/pystardust/ani-cli">ani-cli</a>.

Un ringraziamento speciale a <a href="https://github.com/axtrat">axtrat</a> per l'aiuto nella realizzazione del progetto.
