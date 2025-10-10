# aw-cli

**Guarda anime dal terminale e molto altro.**

**Gli anime vengono presi da [AnimeWorld](https://www.animeworld.tv/)**

## Anteprima

[Guarda l'anteprima su GitHub](https://github.com/fexh10/aw-cli/assets/90156014/88e1c2e2-bb7f-4002-8784-26f70861e164)

## Indice

- [aw-cli](#aw-cli)
  - [Anteprima](#anteprima)
  - [Indice](#indice)
  - [Installazione](#installazione)
    - [Linux e macOS](#linux-e-macos)
    - [Windows](#windows)
      - [Ultima versione (WSL)](#ultima-versione-wsl)
      - [Versione Legacy](#versione-legacy)
    - [Android](#android)
    - [iOS](#ios)
  - [Problemi noti](#problemi-noti)
    - [Linux / Windows WSL](#linux--windows-wsl)
    - [macOS](#macos)
    - [Windows Legacy](#windows-legacy)
  - [Disinstallazione](#disinstallazione)
  - [Utilizzo](#utilizzo)
  - [Crediti](#crediti)

## Installazione

Lo script funziona sia con [MPV](https://mpv.io/installation/) che con [VLC](https://www.videolan.org/vlc/index.it.html).  
È richiesta l'installazione di [fzf](https://github.com/junegunn/fzf?tab=readme-ov-file#installation).

### Linux e macOS

È possibile installare **aw-cli** da `pip`:

```sh
python3 -m pip install aw-cli
```

### Windows

Attualmente Windows presenta due versioni:

- **Ultima versione** (funziona su [WSL](https://learn.microsoft.com/it-it/windows/wsl/install))
- **Legacy** (compatibile con PowerShell, ma non più aggiornata)

#### Ultima versione (WSL)

```sh
wsl --install
python3 -m pip install aw-cli
```

#### Versione Legacy

Richiede [Git per Windows](https://www.git-scm.com/download/win):

```sh
python3 -m pip install git+https://github.com/fexh10/aw-cli.git@winLegacy
```

### Android

Richiede [Termux](https://github.com/termux/termux-app/releases/tag/v0.118.0).

```sh
pkg update && pkg upgrade
pkg install python python-pip fzf
python3 -m pip install aw-cli
```

### iOS

Richiede [iSH](https://apps.apple.com/it/app/ish-shell/id1436902243) e [VLC](https://apps.apple.com/it/app/vlc-media-player/id650377962).

```sh
apk update
apk upgrade
apk add python3 python3-dev py3-pip gcc musl-dev git
python3 -m pip install git+https://github.com/fexh10/aw-cli.git@iosCompatibility
```

> In questo modo è necessario creare e attivare un ambiente virtuale prima di eseguire **aw-cli**.

Oppure, in alternativa:

```sh
apk update
apk upgrade
apk add python3 python3-dev py3-pip gcc musl-dev git pipx
pipx install git+https://github.com/fexh10/aw-cli.git@iosCompatibility
```

Prima di avviare **aw-cli**, è consigliato chiudere e riaprire l’app iSH.  
La velocità di download e caricamento può essere ridotta a causa di iSH, non di **aw-cli**.

## Problemi noti

Se non riesci ad avviare `aw-cli`, probabilmente la cartella degli script Python non è nel tuo `PATH`.

### Linux / Windows WSL

Aggiungi al tuo `.bashrc` o `.zshrc`:

```sh
export PATH=$PATH:$HOME/.local/bin
```

Poi riavvia il terminale o esegui:

```sh
source ~/.bashrc
```

### macOS

```sh
export PATH=$PATH:$HOME/Library/Python/3.x/bin
```

Sostituisci `3.x` con la tua versione di Python, poi riavvia il terminale.

### Windows Legacy

```sh
setx PATH "%PATH%;%APPDATA%\Local\Programs\Python\Python3x\Scripts"
```

Sostituisci `3x` con la tua versione di Python e riavvia se necessario.

## Disinstallazione

```sh
python3 -m pip uninstall aw-cli
```

## Utilizzo

```sh
usage: aw-cli [-h] [-v] [-c [{r}]] [-l [{a,s,d,t}]] [-i] [-s] [-d] [-o] [-p] [-u [UPDATE]] [-a]

Guarda anime dal terminale e molto altro!

Informazioni:
  -h, --help            mostra questo messaggio
  -v, --versione        stampa la versione del programma

Opzioni:
  -c [{r}], --cronologia [{r}]    continua a guardare un anime dalla cronologia. 'r' per rimuovere (opzionale)
  -l [{a,s,d,t}], --lista [{a,s,d,t}]  lista degli ultimi anime usciti. a=all, s=sub, d=dub, t=tendenze
  -i, --info            visualizza le informazioni e la trama di un anime
  -s, --syncplay        usa syncplay per guardare un anime con amici
  -d, --download        scarica gli episodi preferiti
  -o, --offline         apri episodi scaricati dal terminale
  -p, --privato         guarda senza aggiornare la cronologia o AniList
  -u [UPDATE], --update [UPDATE]  aggiorna il programma

Configurazione:
  -a, --configurazione  avvia il menu di configurazione
```

## Crediti

Progetto ispirato a [ani-cli](https://github.com/pystardust/ani-cli).  
Un ringraziamento speciale a [axtrat](https://github.com/axtrat) per l’aiuto nella realizzazione del progetto.
