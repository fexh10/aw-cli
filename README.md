# aw-cli
<h3 align="center">

Guarda anime dal terminale e molto altro!<br /> Gli anime vengono presi da <a href="https://www.animeworld.tv/">AnimeWorld</a>

</h3>

## Anteprima
https://github.com/fexh10/aw-cli/assets/90156014/88e1c2e2-bb7f-4002-8784-26f70861e164

## Indice

- [aw-cli](#aw-cli)
  - [Anteprima](#anteprima)
  - [Indice](#indice)
  - [Installazione](#installazione)
  - [Problemi noti](#problemi-noti)
  - [Disinstallazione](#disinstallazione)
  - [Utilizzo](#utilizzo)
  - [Crediti](#crediti)


## Installazione

Lo script funziona sia con [MPV](https://mpv.io/installation/) che con [VLC](https://www.videolan.org/vlc/index.it.html). <br /> 

È richiesta l'installazione di [fzf](https://github.com/junegunn/fzf?tab=readme-ov-file#installation).<br /> 

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

```
pkg update && pkg upgrade
pkg install python python-pip fzf
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
Nota che la velocità di download e caricamento molto bassa è un problema di iSH e non di aw-cli. 
</details>

## Problemi noti
Se è impossibile avviare `aw-cli`, è possibile che non si abbia la cartella degli script Python aggiunta al path. <br /> 

<details> <summary><b>Linux/Windows WSL</b></summary>
Aggiungere la seguente linea al file di profilo (.bashrc, .zshrc, o altro):

```
export PATH=$PATH:$HOME/.local/bin
```
Riavviare il terminale o eseguire `source ~/.bashrc`.

</details>

<details> <summary><b>MacOS</b></summary>
Aggiungere la seguente linea al file di profilo (.bashrc, .zshrc, o altro):

```
export PATH=$PATH:$HOME/Library/Python/3.x/bin
```
Sostituire `3.x` con la propria versione di Python. <br>
Riavviare il terminale o eseguire `source ~/.bashrc`. 
</details>

<details> <summary><b>Windows Legacy</b></summary>
Inserire da linea di comando:

```
setx PATH "%PATH%;%APPDATA%\Local\Programs\Python\Python3x\Scripts
```
Sostituire `3.x` con la propria versione di Python. <br/>
Se necessario, riavviare il sistema. 
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
