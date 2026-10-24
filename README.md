# aw-cli (Windows Native & Multi-Drive Edition)

<h3 align="center">
Guarda e scarica anime dal terminale su Windows (PowerShell nativo, senza WSL), Linux, macOS e Android!
<br>
Gli anime vengono presi da <a href="https://www.animeworld.ac/">AnimeWorld</a> e <a href="https://www.animeunity.co/">AnimeUnity</a>
</h3>

---

## Novità di questa versione (Windows Nativo + Sicurezza + Multi-Disco)

Rispetto alla versione upstream (che su Windows richiedeva WSL), questa repository integra:
- **Supporto Nativo Windows (PowerShell / CMD / Windows Terminal)** senza bisogno di WSL.
- **Supporto completo per Dischi Secondari (`D:\`, `E:\`, `G:\`, ecc.)**:
  - Possibilità di installare il software e il suo ambiente virtuale su un disco secondario tramite [`install-windows.ps1`](./install-windows.ps1).
  - Scelta interattiva del disco di destinazione per i download degli episodi (`aw-cli -a`) con visualizzazione dello spazio libero in GB su ciascun disco.
  - Ricerca automatica degli eseguibili (`mpv`, `vlc`, `fzf`, `ffmpeg`, `syncplay`) nel `PATH`, nei pacchetti `WinGet` e su **tutti i dischi collegati**.
- **Separazione sicura dei dati utente**: `config.toml` (incluso eventuale token AniList) e `history.json` vengono salvati in `%APPDATA%\aw-cli` (o in `AW_CLI_HOME` per installazioni portabili su disco secondario), evitando il rischio di committare dati personali nella repository.
- **Hardening di Cybersecurity**:
  - Eliminazione di tutte le chiamate `shell=True` vulnerabili a *Command Injection* in `open_vlc` e `open_syncplay`.
  - Protezione contro *Argument Injection* (`--`) verso `mpv` e `vlc`.
  - Validazione rigorosa degli schemi URL (`http`/`https`) sugli embed e sui link video per prevenire SSRF e leak NTLM via UNC path.
  - Prevenzione di *Path Traversal* (`..`), rimozione caratteri di controllo e gestione punti finali nei nomi delle cartelle su Windows.
  - Isolamento del server di reload di `fzf` esclusivamente su loopback (`127.0.0.1`) e pulizia automatica dei file temporanei.

---

## Installazione

### Windows (PowerShell Nativo — Consigliato)

#### Metodo 1: Installer automatico interattivo (supporta anche dischi secondari)
Clona la repository ed esegui lo script PowerShell:
```powershell
git clone https://github.com/fexh10/aw-cli.git
cd aw-cli
powershell -ExecutionPolicy Bypass -File .\install-windows.ps1
```
Lo script ti permetterà di scegliere:
1. Se installare il programma nel percorso standard o su un **disco secondario** (es. `D:\aw-cli`).
2. Su quale **disco salvare gli anime scaricati** (es. `D:\Anime`).

Puoi anche passare i parametri direttamente da riga di comando:
```powershell
.\install-windows.ps1 -InstallDir "D:\aw-cli" -DownloadDir "D:\Anime" -Provider "animeunity"
```

#### Metodo 2: Installazione diretta con `pip` o `uv`
Assicurati di avere installati `fzf`, `mpv` (o `vlc`) e `ffmpeg`:
```powershell
winget install junegunn.fzf mpv-player.mpv-CI.MSVC Gyan.FFmpeg
pip install .
```

---

### Linux, macOS, Windows (WSL)

È consigliato installare tramite `uv` o `pip`:
```bash
uv tool install .
# oppure
pipx install .
```

### Android (Termux)
```bash
pkg update && pkg upgrade
pkg install python3 fzf uv
uv tool install .
```

---

## Configurazione e Scelta del Disco Secondario

In qualsiasi momento puoi aprire il menu di configurazione con:
```powershell
aw-cli -a
```
Dal menu potrai:
- Scegliere il player (`mpv` o `vlc`).
- Scegliere il provider (`animeunity` o `animeworld`).
- **Scegliere il disco o la cartella per i download** (vengono elencati automaticamente tutti i dischi del PC con i GB liberi, più l'opzione per inserire un percorso personalizzato).
- Configurare la sincronizzazione automatica con **AniList**.

### Variabili d'ambiente supportate
- `AW_CLI_HOME`: sposta la cartella di configurazione e cronologia (`config.toml` e `history.json`) in qualsiasi percorso o disco secondario (es. `D:\aw-cli\data`).
- `AW_CLI_DOWNLOAD_DIR`: sovrascrive la cartella di download degli episodi.

---

## Utilizzo
```text
usage: aw-cli [-h] [-v] [-c [{r}]] [-l [{a,s,d,t}]] [-i] [-s] [-d] [-o] [-p] [-u [UPDATE]] [-a]

Guarda anime dal terminale e molto altro!

Informazioni:
  -h, --help            mostra questo messaggio
  -v, --versione        stampa la versione del programma

Opzioni:
  -c [{r}], --cronologia [{r}]
                        continua a guardare un anime dalla cronologia. 'r' per
                        rimuovere un anime (opzionale)
  -l [{a,s,d,t}], --lista [{a,s,d,t}]
                        lista degli ultimi anime usciti. Filtri: a = all, s =
                        sub, d = dub, t = tendenze. Default 'a'
  -i, --info            visualizza le informazioni e la trama di un anime
  -s, --syncplay        usa syncplay per guardare un anime insieme ai tuoi
                        amici
  -d, --download        scarica gli episodi che preferisci
  -o, --offline         apri gli episodi scaricati precedentemente
                        direttamente dal terminale
  -p, --privato         guarda un episodio senza che si aggiorni la cronologia
                        o AniList
  -u [UPDATE], --update [UPDATE]
                        aggiorna il programma

Configurazione:
  -a, --configurazione  avvia il menu di configurazione
```

---

## Crediti e Licenza

- Progetto originale ideato e sviluppato da **[fexh10](https://github.com/fexh10/aw-cli)** (con il contributo di [axtrat](https://github.com/axtrat)), ispirato a [ani-cli](https://github.com/pystardust/ani-cli).
- Rilasciato sotto licenza **[GNU GPL v3.0](./LICENSE)**.
