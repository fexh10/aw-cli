# aw-cli
<h3 align="center">

Guarda anime dal terminale e molto altro!

 Gli anime vengono presi da [Animeworld](https://www.animeworld.ac/) e [Animeunity](https://www.animeunity.so/)

</h3>

## Anteprima
https://github.com/fexh10/aw-cli/assets/90156014/88e1c2e2-bb7f-4002-8784-26f70861e164

## Indice

- [aw-cli](#aw-cli)
  - [Anteprima](#anteprima)
  - [Indice](#indice)
  - [Installazione](#installazione)
  - [Problemi noti](#problemi-noti)
  - [Utilizzo](#utilizzo)
  - [Crediti](#crediti)


## Installazione

Lo script funziona sia con [MPV](https://mpv.io/installation/) che con [VLC](https://www.videolan.org/vlc/index.it.html).

È richiesta l'installazione di [fzf](https://github.com/junegunn/fzf?tab=readme-ov-file#installation).

<details><summary><b>Linux, MacOS, Windows WSL</b></summary>

È consigliato installare `aw-cli` tramite [uv](https://github.com/astral-sh/uv):

```
uv tool install aw-cli
```

In alternativa, è possibile usare [pipx](https://pipx.pypa.io/latest/installation/):

```
pipx install aw-cli
```

</details>

<details><summary><b>Windows</b></summary>

Il supporto per Windows è mantenuto solamente tramite WSL. Nel caso si voglia usare Powershell, è possibile installare la versione Legacy, che non riceverà più aggiornamenti. È necessario avere [git](https://www.git-scm.com/download/win) e [uv](https://github.com/astral-sh/uv):

```
uv tool install git+https://github.com/fexh10/aw-cli.git@winLegacy
```

In alternativa è possibile usare [pipx](https://pipx.pypa.io/latest/installation/):

```
pipx install git+https://github.com/fexh10/aw-cli.git@winLegacy
```

</details>
</details>

<details><summary><b>Android</b></summary>

Android richiede l'installazione di [Termux](https://github.com/termux/termux-app/releases).

```
pkg update && pkg upgrade
pkg install python3 fzf uv
uv tool install aw-cli
```

</details>

## Problemi noti

- Se è impossibile avviare `aw-cli`, è possibile che non si abbia la cartella degli script Python aggiunta al path. <br /> 

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

- Se il programma si avvia ma appare "Errore di connessione", potrebbe essere un problema relativo ai certificati SSL. Scaricare il certificato `SSL.com TLS Transit ECC CA R2` al seguente [link](https://ssl.com/repo/certs/SSL.com-TLS-T-ECC-R2.pem) ed eseguire il comando:

  ```bash
  trust anchor SSL.com-TLS-T-ECC-R2.pem
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
                        lista degli ultimi anime usciti. Filtri: a = all, s = sub, d = dub, t = tendenze. Default 'a'
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

Progetto ispirato a [ani-cli](https://github.com/pystardust/ani-cli).

Un ringraziamento speciale a [axtrat](https://github.com/axtrat) per l'aiuto nella realizzazione del progetto.
