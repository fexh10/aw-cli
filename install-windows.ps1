<#
.SYNOPSIS
    Installer nativo Windows per aw-cli con supporto completo per dischi secondari (D:\, E:\, ecc.).
.DESCRIPTION
    Permette di installare aw-cli (ambiente Python, configurazione, cronologia e cartella download)
    sia nel percorso predefinito sia su qualsiasi disco secondario.
.PARAMETER InstallDir
    Cartella di installazione del software (es. "D:\aw-cli"). Se omesso, viene chiesto interattivamente.
.PARAMETER DownloadDir
    Cartella dove salvare gli episodi scaricati (es. "D:\Anime"). Se omesso, viene chiesto interattivamente.
.PARAMETER Provider
    Provider predefinito ("animeunity" o "animeworld"). Default: "animeunity".
#>
param(
    [string]$InstallDir = "",
    [string]$DownloadDir = "",
    [ValidateSet("animeunity", "animeworld")]
    [string]$Provider = "animeunity"
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "   AW-CLI - INSTALLER NATIVO WINDOWS (MULTI-DISCO)  " -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan

# 1. Rileva tutti i dischi disponibili
$drives = Get-PSDrive -PSProvider FileSystem | Where-Object { $_.Free -ne $null } | Select-Object Name, Root, @{N="FreeGB";E={[math]::Round($_.Free / 1GB, 1)}}
Write-Host "`nDischi rilevati sul sistema:" -ForegroundColor Yellow
for ($i = 0; $i -lt $drives.Count; $i++) {
    $d = $drives[$i]
    Write-Host ("  [{0}] Disco {1} ({2} GB liberi)" -f ($i + 1), $d.Root, $d.FreeGB)
}

# 2. Scelta del disco/percorso di installazione del software
if (-not $InstallDir) {
    Write-Host "`nDove vuoi installare il software aw-cli?" -ForegroundColor Green
    Write-Host "  [0] Installazione standard nell'ambiente Python corrente"
    for ($i = 0; $i -lt $drives.Count; $i++) {
        $d = $drives[$i]
        Write-Host ("  [{0}] Installa su {1}aw-cli ({2} GB liberi)" -f ($i + 1), $d.Root, $d.FreeGB)
    }
    Write-Host "  [P] Percorso personalizzato"
    $choice = Read-Host "Scelta (predefinito: 0)"
    if ($choice -eq "P" -or $choice -eq "p") {
        $InstallDir = Read-Host "Inserisci il percorso di installazione (es. D:\Apps\aw-cli)"
    } elseif ($choice -match '^\d+$' -and [int]$choice -ge 1 -and [int]$choice -le $drives.Count) {
        $selectedRoot = $drives[[int]$choice - 1].Root
        $InstallDir = Join-Path $selectedRoot "aw-cli"
    }
}

# 3. Scelta del disco/cartella per i download degli anime
if (-not $DownloadDir) {
    $defaultDl = Join-Path $env:USERPROFILE "Videos\Anime"
    Write-Host "`nDove vuoi salvare gli episodi scaricati?" -ForegroundColor Green
    Write-Host "  [0] Cartella predefinita ($defaultDl)"
    for ($i = 0; $i -lt $drives.Count; $i++) {
        $d = $drives[$i]
        Write-Host ("  [{0}] Disco {1}Anime ({2} GB liberi)" -f ($i + 1), $d.Root, $d.FreeGB)
    }
    Write-Host "  [P] Percorso personalizzato"
    $dlChoice = Read-Host "Scelta (predefinito: 0)"
    if ($dlChoice -eq "P" -or $dlChoice -eq "p") {
        $DownloadDir = Read-Host "Inserisci il percorso per i download (es. D:\Anime)"
    } elseif ($dlChoice -match '^\d+$' -and [int]$dlChoice -ge 1 -and [int]$dlChoice -le $drives.Count) {
        $selectedRoot = $drives[[int]$dlChoice - 1].Root
        $DownloadDir = Join-Path $selectedRoot "Anime"
    } else {
        $DownloadDir = $defaultDl
    }
}

# 4. Verifica e installazione dipendenze esterne (fzf, mpv) tramite winget
Write-Host "`nVerifica dipendenze multimediali (fzf, mpv)..." -ForegroundColor Cyan
if (-not (Get-Command fzf -ErrorAction SilentlyContinue)) {
    Write-Host "Installazione di fzf tramite winget..." -ForegroundColor Yellow
    winget install --id junegunn.fzf --accept-package-agreements --accept-source-agreements
}
if (-not (Get-Command mpv -ErrorAction SilentlyContinue)) {
    Write-Host "Installazione di mpv tramite winget..." -ForegroundColor Yellow
    winget install --id mpv-player.mpv-CI.MSVC --accept-package-agreements --accept-source-agreements
}

# 5. Installazione del pacchetto Python (standard o su disco secondario)
$repoRoot = $PSScriptRoot
if ($InstallDir) {
    Write-Host "`nInstallazione di aw-cli su '$InstallDir'..." -ForegroundColor Cyan
    New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
    $venvDir = Join-Path $InstallDir ".venv"
    $dataDir = Join-Path $InstallDir "data"
    $binDir  = Join-Path $InstallDir "bin"
    New-Item -ItemType Directory -Force -Path $dataDir | Out-Null
    New-Item -ItemType Directory -Force -Path $binDir | Out-Null

    python -m venv $venvDir
    $venvPython = Join-Path $venvDir "Scripts\python.exe"
    & $venvPython -m pip install --upgrade pip
    & $venvPython -m pip install $repoRoot

    # Crea il launcher aw-cli.cmd nella cartella bin del disco scelto
    $venvAwCli = Join-Path $venvDir "Scripts\aw-cli.exe"
    $launcherPath = Join-Path $binDir "aw-cli.cmd"
    @"
@echo off
set "PYTHONUTF8=1"
set "AW_CLI_HOME=$dataDir"
"$venvAwCli" %*
"@ | Set-Content -Path $launcherPath -Encoding UTF8

    # Aggiunge $binDir al PATH utente se non presente
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($userPath -notlike "*$binDir*") {
        [Environment]::SetEnvironmentVariable("Path", "$binDir;$userPath", "User")
    }
    [Environment]::SetEnvironmentVariable("AW_CLI_HOME", $dataDir, "User")
    $env:AW_CLI_HOME = $dataDir
    $activePython = $venvPython
} else {
    Write-Host "`nInstallazione di aw-cli nell'ambiente Python utente..." -ForegroundColor Cyan
    python -m pip install $repoRoot
    $activePython = "python"
}

[Environment]::SetEnvironmentVariable("PYTHONUTF8", "1", "User")
$env:PYTHONUTF8 = "1"

# 6. Genera la configurazione iniziale con il disco di download scelto
& $activePython -c @"
import aw_cli.utilities as ut
from pathlib import Path

config_path = ut.get_config_path()
mpv_path = ut.find_binary('mpv') or 'mpv'
dl_dir = r'''$DownloadDir'''
Path(dl_dir).mkdir(parents=True, exist_ok=True)

cfg = {
    'player': {'type': 'mpv', 'path': mpv_path},
    'provider': {'source': '$Provider'},
    'general': {
        'specials': False,
        'download-path': dl_dir,
        'connections-per-download': 4,
        'parallel-downloads': 3,
    },
    'style': ut.DEFAULT_STYLE,
}
with open(config_path, 'w', encoding='utf-8') as f:
    ut.toml.dump(cfg, f)
print('Configurazione salvata in:', config_path)
print('Cartella download impostata su:', dl_dir)
"@

Write-Host "`nInstallazione completata con successo! Digita 'aw-cli' per iniziare." -ForegroundColor Green
