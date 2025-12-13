import os
import asyncio
from pathlib import Path
from httpx import AsyncClient
from rich.progress import Progress, BarColumn, TextColumn, TaskID, DownloadColumn, TransferSpeedColumn
from . import utilities as ut
from .anime import Anime
from .providers import Provider

def path(create: bool = True) -> str:
    """
    Restituisce il percorso di download dell'anime, a seconda del sistema operativo in uso.
    Se create è True (valore predefinito) e il percorso non esiste, viene creato.

    Args:
        create (bool, optional): se impostato a True, crea il percorso se non esiste. Valore predefinito: True.

    Returns:
        str: il percorso di download dell'anime.
    """

    if (ut.nome_os == "Android"):
        path = "/sdcard/Movies/Anime"
    else:
        path = f"{Path.home()}/Videos/Anime"
    if create and not os.path.exists(path):
        os.makedirs(path)
    return path


def episodes(anime: Anime, episodes: list[Anime.Episode], provider: Provider):
    """
    Scarica più episodi in modo concorrente (max concurrent_downloads).
    """
    async def download_worker(ep: Anime.Episode, task_id: TaskID, progress: Progress, sem: asyncio.Semaphore):
        async with sem:
            filename = f"{path()}/{anime.name}/{ep}.mp4"
            if os.path.exists(filename):
                progress.update(task_id, completed=100, total=100, description=f"[green]Ep. {ep.num} (Esistente)")
                return

            os.makedirs(os.path.dirname(filename), exist_ok=True)
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
                        with open(filename + ".temp", "wb") as f:
                            async for chunk in response.aiter_bytes(1024):
                                if chunk:
                                    n = f.write(chunk)
                                    downloaded += n
                                    progress.update(task_id, advance=n)

                os.rename(filename + ".temp", filename)
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
