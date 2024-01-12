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

<details><summary><b>Linux, MacOS</b></summary>
È possibile installare aw-cli da pip:

```
python3 -m pip install aw-cli
```
</details>

<details><summary><b>Windows</b></summary>
Attualmente, Windows presenta due versioni: la più recente, progettata per funzionare su WSL (Windows Subsystem for Linux), e una versione Legacy compatibile con PowerShell. La versione Legacy non riceverà ulteriori aggiornamenti, mentre l'altra sarà mantenuta costantemente. 

<br>

<details><summary><b>Ultima Versione</b></summary>
L'ultima versione per Windows richiede installare <a href="https://learn.microsoft.com/it-it/windows/wsl/install">WSL</a>:

```
wsl --install
```
Per installare MPV su WSL, basta eseguire:
```
sudo apt install mpv
``` 

Per VLC:
```
sudo apt install vlc
```

Il programma dovrà essere installato e avviato da WSL:

```
python3 -m pip install aw-cli
```
</details>
<details><summary><b>Versione Legacy</b></summary>
Per installare la versione Legacy, è necessario avere <a href="https://www.git-scm.com/download/win">git</a>.


```
python3 -m pip install git+https://github.com/fexh10/aw-cli.git@winLegacy
```

</details>
</details>

<details><summary><b>Android</b></summary>
Android richiede l'installazione di <a href="https://github.com/termux/termux-app/releases/tag/v0.118.0">termux</a>. <br>
È possibile installare aw-cli da pip:

```
python3 -m pip install aw-cli
```
</details>

<details><summary><b>iOS</b></summary>
La versione per iOS richiede <a href="https://apps.apple.com/it/app/ish-shell/id1436902243">iSH</a> e <a href="https://apps.apple.com/it/app/vlc-media-player/id650377962">VLC</a>. 

```
apk update
apk upgrade
apk add python3 python3-dev py3-pip gcc musl-dev git
python3 -m pip install git+https://github.com/fexh10/aw-cli.git@iosCompatibility
```

</details>

## Disinstallazione 

```
python3 -m pip uninstall aw-cli
```

## Utilizzo
```
usage: aw-cli [-h] [-v] [-c [{r}]] [-l [{a,s,d,t}]] [-i] [-s] [-d] [-o] [-p] [-u [UPDATE]] [-a]

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
  -u [UPDATE], --update [UPDATE]
                        aggiorna il programma

Configurazione:
  -a, --configurazione  avvia il menu di configurazione                                                    
```

## Crediti
Progetto ispirato a <a href="https://github.com/pystardust/ani-cli">ani-cli</a>.

Un ringraziamento speciale a <a href="https://github.com/axtrat">axtrat</a> per l'aiuto nella realizzazione del progetto.
