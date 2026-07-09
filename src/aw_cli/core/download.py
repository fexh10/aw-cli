import asyncio
from pathlib import Path
from httpx import AsyncClient
from rich.progress import Progress, BarColumn, TextColumn, TaskID, DownloadColumn, TransferSpeedColumn
from ..interface import console
from .config import config
from .env import env
from .anime import Anime
from ..providers import Provider

def get_anime_dir(anime: Anime, create: bool = True) -> Path:
    """
    Restituisce la cartella di download specifica per l'anime,
    sanitizzando il nome per i vincoli del filesystem.
    """
    sanitized_name = env.sanitize_filename(anime.name)
    anime_dir = config.download_path / sanitized_name
    if create:
        anime_dir.mkdir(parents=True, exist_ok=True)
    return anime_dir

def get_episode_path(anime: Anime, ep: Anime.Episode, create: bool = True) -> Path:
    """
    Restituisce il percorso completo sul filesystem del file dell'episodio,
    sanitizzando sia la cartella dell'anime che il nome del file .mp4.
    """
    anime_dir = get_anime_dir(anime, create=create)
    sanitized_filename = env.sanitize_filename(f"{ep}.mp4")
    return anime_dir / sanitized_filename

def episodes(anime: Anime, episodes: list[Anime.Episode], provider: Provider) -> None:
    """
    Scarica più episodi in modo concorrente (max concurrent_downloads).

    Args:
        anime (Anime): l'anime di cui scaricare gli episodi.
        episodes (list[Anime.Episode]): la lista degli episodi da scaricare.
        provider (Provider): il provider da cui scaricare gli episodi.
    """
    async def download_worker(ep: Anime.Episode, task_id: TaskID, progress: Progress, sem: asyncio.Semaphore):
        async with sem:
            filename = get_episode_path(anime, ep)
            if filename.exists():
                progress.update(task_id, completed=100, total=100, description=f"[success]Ep. {ep.num} (Esistente)")
                return

            filename.parent.mkdir(parents=True, exist_ok=True)
            try:
                url = provider.episode_link(anime, ep)
            except Exception as e:
                progress.console.print(f"[error]Errore link Ep. {ep.num}: {e}")
                return

            try:
                async with AsyncClient() as client:
                    async with client.stream("GET", url, headers=provider.Client.headers) as response:
                        total = int(response.headers.get('content-length', 0))
                        progress.update(task_id, total=total)

                        downloaded = 0
                        temp_filename = filename.with_name(f"{filename.name}.temp")
                        with open(temp_filename, "wb") as f:
                            async for chunk in response.aiter_bytes(1024):
                                if chunk:
                                    n = f.write(chunk)
                                    downloaded += n
                                    progress.update(task_id, advance=n)

                temp_filename.rename(filename)
                progress.update(task_id, description=f"[success]Ep. {ep.num} (Completato)[/]")
            except Exception as e:
                progress.console.print(f"[error]Errore download Ep. {ep.num}: {e}[/]")

    async def _download_all():
        concurrent_downloads = config.data["general"].get("parallel-downloads", 3)
        semaphore = asyncio.Semaphore(concurrent_downloads)
        ordered_eps = sorted(episodes, key=lambda e: e.numeric())

        with Progress(
            TextColumn("[info]{task.description}[/]", style="info"),
            BarColumn(bar_width=None),
            "•",
            DownloadColumn(),
            "•",
            TransferSpeedColumn(),
            console=console,
        ) as progress:
            tasks = []
            for ep in ordered_eps:
                task_id = progress.add_task(str(ep), total=None, start=True)
                tasks.append(asyncio.create_task(download_worker(ep, task_id, progress, semaphore)))

            await asyncio.gather(*tasks)

    asyncio.run(_download_all())
