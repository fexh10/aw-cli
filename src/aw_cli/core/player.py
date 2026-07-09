import re
import subprocess
from .config import config

def open_player(ep_url: str, ep_name: str, progress: int, syncplay: bool) -> tuple[bool, int]:
    """
    Decide ed avvia il player corretto in base alle condizioni e alla configurazione.
    """
    player_type = config.data["player"].get("type")

    if player_type == "android":
        return android_player(ep_url, ep_name, progress)

    if syncplay and config.data.get("syncplay", {}).get("path"):
        return open_syncplay(ep_url, ep_name, progress)

    return open_mpv(ep_url, ep_name, progress)


def android_player(ep_url: str, ep_name: str, progress: int) -> tuple[bool, int]:
    """
    Avvia il player predefinito su Android.

    Args:
        ep_url (str): l'URL dell'episodio da riprodurre.
        ep_name (str): il nome dell'episodio.
        progress (int): il progresso dell'episodio.

    Returns:
        bool: True se l'episodio è stato riprodotto completamente, altrimenti False.
        int: il progresso dell'episodio.
    """
    subprocess.run(
        f'am start --user 0 -a android.intent.action.VIEW -d "{ep_url}" -n org.videolan.vlc/.StartActivity -e "title" "{ep_name}"',
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return True, 0


def open_syncplay(ep_url: str, ep_name: str, progress: int) -> tuple[bool, int]:
    """
    Avvia Syncplay.

    Args:
        ep_url (str): l'URL dell'episodio da riprodurre.
        ep_name (str): il nome dell'episodio.
        progress (int): il progresso dell'episodio.

    Returns:
        bool: True se l'episodio è stato riprodotto completamente, altrimenti False.
        int: il progresso dell'episodio.
    """

    player_path = config.player_path
    player_arg = f'--player-path "{player_path}"'
    args = f'''--force-media-title="{ep_name}" --start="{progress}" --fullscreen --keep-open'''

    try:
        command = f'''{config.syncplay_path} {player_arg} -d --language it "{ep_url}" -- {args}'''
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, errors="replace", check=False
        )
        out = result.stdout + "\n" + result.stderr
    except Exception as e:
        raise RuntimeError(f"Impossibile avviare il processo Syncplay: {e}")

    duration_match = re.findall(r'duration(?:-change)?"?:?[\s=:]+(\d+)\.?[\d]*', out)
    progress_match = re.findall(r'pos(?:ition"?)?[\s=:]+(\d+)\.?[\d]*', out)
    if not duration_match:
        raise RuntimeError(
            f"Impossibile leggere l'output di Syncplay!\n"
            f"stdout={result.stdout!r}\n"
            f"stderr={result.stderr!r}\n"
        )
    duration = max(map(int, duration_match))
    progress_match = list(filter(lambda x: x > 0, map(int, progress_match)))
    progress = progress_match[-1] if progress_match else 0

    return (
        progress * 100 // duration >= config.data["player"]["complete_limit"] if duration > 0 else False,
        progress,
    )


def open_mpv(ep_url: str, ep_name: str, progress: int) -> tuple[bool, int]:
    """
    Apre MPV per riprodurre il video.

    Args:
        ep_url (str): il link del video o il percorso del file.
        ep_name (str): il nome del video.
        progress (int): il progresso dell'episodio.

    Returns:
        bool: True se l'episodio è stato riprodotto completamente, altrimenti False.
        int: il progresso dell'episodio.
    """

    command = [
        config.player_path,
        ep_url,
        f"--force-media-title={ep_name}",
        f"--start={progress}",
        "--fullscreen",
        "--keep-open",
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)

    if res := re.findall(r"(\d+):(\d+):(\d+) / [\d:]+ \((\d+)%\)", result.stdout):
        last = res[-1]
        return (
            int(last[3]) >= config.data["player"]["complete_limit"],
            ((int(last[0]) * 3600) + (int(last[1]) * 60) + int(last[2])),
        )

    raise RuntimeError(
        f"Impossibile leggere l'output di MPV durante la riproduzione di {ep_url}! "
        f"returncode={result.returncode}\n"
        f"stdout={result.stdout!r}\n"
    )
