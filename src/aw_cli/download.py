import os
import asyncio
from pathlib import Path
from httpx import AsyncClient
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
    Scarica più episodi in modo concorrente (max concurrent_downloads),
    mantenendo l'ordine (ep.numeric()) e mostrando una barra ASCII colorata.
    """

    async def render(progress: list[int], episodes: list[Anime.Episode]):
        while any(p < 100 for p in progress):
            ut.my_print(anime.name, color="blu",cls=True)
            for ep, perc in zip(episodes, progress):
                # barra ASCII
                bar_len = 50
                filled = perc * bar_len // 100
                bar = "#" * filled + "-" * (bar_len - filled)

                # se completato → verde, altrimenti giallo
                bar_color = "verde" if perc == 100 else "giallo"

                ut.my_print(f"Ep. {ep.num}", color="blu", end=" ")
                ut.my_print("[", end="")
                ut.my_print(f"{bar}", color=bar_color, end="")
                ut.my_print(f"] {perc:3d}%")

            await asyncio.sleep(0.2)
        # Render finale per mostrare tutto verde
        ut.my_print(anime.name, color="blu", cls=True)
        for ep in episodes:
            ut.my_print(f"Ep. {ep.num}", color="blu", end=" ")
            ut.my_print("[", end="")
            ut.my_print(f"{'#' * 50}", color="verde", end="")
            ut.my_print("] 100%")

    async def worker(ep: Anime.Episode, i: int, progress: list[int], semaphore: asyncio.Semaphore):
        try:
            ok = await episode(anime, ep, provider, f"{path()}/{anime.name}", i, progress)
            if ok:
                progress[i] = 100
        finally:
            semaphore.release()

    async def _download_all():
        concurrent_downloads = ut.configData["general"].get("parallel-downloads", 3)
        semaphore = asyncio.Semaphore(concurrent_downloads)

        # ordino gli episodi per numero
        ordered_eps = sorted(episodes, key=lambda e: e.numeric())
        progress = [0] * len(ordered_eps)

        # avvio render + download
        render_task = asyncio.create_task(render(progress, ordered_eps))
        tasks: list[asyncio.Task[None]] = []
        for i, ep in enumerate(ordered_eps):
            await semaphore.acquire()
            tasks.append(asyncio.create_task(worker(ep, i, progress, semaphore)))

        await asyncio.gather(*tasks)
        await render_task  # chiude il render quando tutto è completo

    asyncio.run(_download_all())


async def episode(anime: Anime, ep: Anime.Episode, provider: Provider, path: str, task_id: int, progress: list[int]):
    filename = f"{path}/{ep}.mp4"
    if os.path.exists(filename):
        progress[task_id] = 100
        return False
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    url = provider.episode_link(anime, ep)
    async with AsyncClient() as client:
        async with client.stream("GET", url, headers=provider.Client.headers) as response:
            total = int(response.headers.get('content-length', 0))
            downloaded = 0
            with open(filename + ".temp", "wb") as f:
                async for chunk in response.aiter_bytes(1024):
                    if chunk:
                        downloaded += f.write(chunk)
                        if total:
                            progress[task_id] = int(downloaded * 100 / total)
    os.rename(filename + ".temp", filename)
    return True
