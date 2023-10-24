# aw-cli
<h3 align="center">

Guarda anime dal terminale e molto altro!<br /> Gli anime vengono presi da <a href="https://www.animeworld.tv/">AnimeWorld</a>

</h3>

## Anteprima
https://user-images.githubusercontent.com/90156014/210212814-e73ba7af-ce12-43ad-95ff-dcd85b39a45c.mp4

## Indice

- [Installazione](#Installazione)
- [Disinstallazione](#Disinstallazione)
- [Utilizzo](#Utilizzo)
- [Crediti](#Crediti)
- [Disclaimer](./disclaimer.md)


## Installazione

Lo script funziona sia con [MPV](https://mpv.io/installation/) che con [VLC](https://www.videolan.org/vlc/index.it.html). <br /> 
Se si utilizza Windows e MPV, occorrerà scaricare inoltre "mpv-2.dll" (scaricabile da questo [link](https://sourceforge.net/projects/mpv-player-windows/files/libmpv/)) e aggiungerlo al path.

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
usage: aw-cli [-h] [-a] [-c] [-d] [-i] [-l [{a,s,d,t}]] [-o] [-p] [-s] [-v]

Guarda anime dal terminale e molto altro!

options:
  -h, --help            show this help message and exit
  -a, --configurazione  avvia il menu di configurazione
  -c, --cronologia      continua a guardare un anime dalla cronologia
  -d, --download        scarica gli episodi che preferisci
  -i, --info            visualizza le informazioni e la trama di un anime
  -l [{a,s,d,t}], --lista [{a,s,d,t}]
                        lista degli ultimi anime usciti su AnimeWorld. a = all, s = sub, d =
                        dub, t = tendenze. Default 'a'
  -o, --offline         apri gli episodi scaricati precedentemente direttamente dal terminale
  -p, --privato         guarda un episodio senza che si aggiorni la cronologia o AniList
  -s, --syncplay        usa syncplay per guardare un anime insieme ai tuoi amici
  -v, --versione        stampa la versione del programma
                                                             
```

## Crediti
Progetto ispirato a <a href="https://github.com/pystardust/ani-cli">ani-cli</a>.

Un ringraziamento speciale a <a href="https://github.com/axtrat">axtrat</a> per l'aiuto nella realizzazione del progetto.
