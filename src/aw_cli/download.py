import asyncio
from pathlib import Path
from httpx import AsyncClient
from rich.progress import Progress, BarColumn, TextColumn, TaskID, DownloadColumn, TransferSpeedColumn
from . import utilities as ut
from .anime import Anime
from .providers import Provider

from functools import lru_cache

@lru_cache
def path(create: bool = True) -> Path:
    """
    Restituisce il percorso di download dell'anime, a seconda del sistema operativo in uso.
    Se create è True (valore predefinito) e il percorso non esiste, viene creato.

    Args:
        create (bool, optional): se impostato a True, crea il percorso se non esiste. Valore predefinito: True.

    Returns:
        Path: il percorso di download dell'anime.
    """

    if (ut.nome_os == "Android"):
        path = Path("/sdcard/Movies/Anime")
    else:
        path = Path.home() / "Videos/Anime"

    if create:
        path.mkdir(parents=True, exist_ok=True)
    return path


def episodes(anime: Anime, episodes: list[Anime.Episode], provider: Provider):
    """
    Scarica più episodi in modo concorrente (max concurrent_downloads).
    """
    async def download_worker(ep: Anime.Episode, task_id: TaskID, progress: Progress, sem: asyncio.Semaphore):
        async with sem:
            filename = path() / anime.name / f"{ep}.mp4"
            if filename.exists():
                progress.update(task_id, completed=100, total=100, description=f"[green]Ep. {ep.num} (Esistente)")
                return

            filename.parent.mkdir(parents=True, exist_ok=True)
            try:
                url = provider.episode_link(anime, ep)
            except Exception as e:
                progress.console.print(f"[red]Errore link Ep. {ep.num}: {e}")
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
        concurrent_downloads = ut.configData["general"].get("parallel-downloads", 3)
        semaphore = asyncio.Semaphore(concurrent_downloads)
        ordered_eps = sorted(episodes, key=lambda e: e.numeric())

        with Progress(
            TextColumn("[info]{task.description}[/]", style="info"),
            BarColumn(bar_width=None),
            "•",
            DownloadColumn(),
            "•",
            TransferSpeedColumn(),
            console=ut.console,
        ) as progress:
            tasks = []
            for ep in ordered_eps:
                task_id = progress.add_task(str(ep), total=None, start=True)
                tasks.append(asyncio.create_task(download_worker(ep, task_id, progress, semaphore)))

            await asyncio.gather(*tasks)

    asyncio.run(_download_all())
