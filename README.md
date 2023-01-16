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

Lo script funziona tramite il lettore video <a href="https://mpv.io/installation/">MPV</a>, quindi installarlo se non lo si ha già. <br /> 
Su Windows, inoltre, occorre installare "mpv-2.dll", scaricabile da questo [link](https://sourceforge.net/projects/mpv-player-windows/files/libmpv/), e copiarlo nella stessa directory dello script.

È possibile installare aw-cli da sorgente (potrebbe essere più aggiornato):
```
python3 -m pip install git+https://github.com/fexh10/aw-cli.git
```
O se si preferisce da pip:
```
python3 -m pip install aw-cli --upgrade
```
## Disinstallazione 

```
python3 -m pip uninstall aw-cli
```

## Utilizzo
```
usage: aw-cli [-h] [-c] [-d] [-l [{a,s,d}]] [-o] [-s]

Guarda anime dal terminale e molto altro!

options:
  -h, --help            show this help message and exit
  -c, --cronologia      continua a guardare un anime dalla cronologia
  -d, --download        scarica gli episodi che preferisci
  -l [{a,s,d}], --lista [{a,s,d}]
                        lista degli ultimi anime usciti su AnimeWorld. a = all, s = sub, d = dub
  -o, --offline         apri gli episodi scaricati precedentemente direttamente dal terminale
  -s, --syncplay        usa syncplay per guardare un anime insieme ai tuoi amici
                                                             
```

## Crediti
Progetto ispirato a <a href="https://github.com/pystardust/ani-cli">ani-cli</a>.

Un ringraziamento speciale a <a href="https://github.com/axtrat">axtrat</a> per l'aiuto nella realizzazione del progetto.
