# aw-cli
<h3 align="center">
Guarda anime dal terminale e molto altro!\n Gli anime vengono presi da <a href="animeworld.tv/">AnimeWorld</a>

</h3>

## Indice

- [Installazione](#Installazione)
- [Disinstallazione](#Disintallazione)
- [Utilizzo](#Utilizzo)
- [Crediti](#Crediti)


## Installazione

Lo script funziona tramite il lettore video <a href="https://mpv.io/installation/">MPV.</a>, quindi installarlo se non lo si ha già.
N.B.: Su Android il lettore video è <a href="https://play.google.com/store/apps/details?id=org.videolan.vlc&hl=it&gl=US">VLC.</a>
È possibile installare aw-cli da pip:
```
python3 -m pip install aw-cli --upgrade
```
O si se preferisce da sorgente (potrebbe essere più aggiornato):
```
python3 -m pip install git+https://github.com/fexh10/aw-cli.git
```
## Disinstallazione 

```
python3 -m pip uninstall aw-cli
```

##Utilizzo
```
usage: aw-cli [-h] [-s] [-d] [-l [{a,s,d}]]

Guarda anime dal terminale e molto altro!

options:
  -h, --help            show this help message and exit
  -s, --syncplay        usa syncplay per guardare un anime insieme ai tuoi amici
  -d, --download        scarica gli episodi che preferisci
  -l [{a,s,d}], --lista [{a,s,d}]
                        lista degli ultimi anime usciti su AnimeWorld. a = all, s = sub, d = dub
```

##Crediti
Progetto ispirato da <a href="https://github.com/pystardust/ani-cli">ani-cli</a>.

Un ringraziamento speciale a <a href="https://github.com/axtrat">axtrat</a> per l'aiuto nella realizzazione del progetto.
