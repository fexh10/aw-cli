
"""
Download degli episodi forniti come stream invece che come file video diretto.

Gli stream HLS (.m3u8) vengono scaricati con ffmpeg, senza ricodificare.
I link YouTube non sono supportati e vengono segnalati con un errore chiaro.
"""

import asyncio
import re
import shutil
from pathlib import Path
from urllib.parse import urljoin, urlparse
from httpx import AsyncClient, Headers
from rich.progress import Progress, TaskID

def is_hls(url: str) -> bool:
  """Indica se il link è una playlist HLS (.m3u8)."""
  return urlparse(url).path.endswith(".m3u8")

def is_youtube(url: str) -> bool:
  """Indica se il link punta a un video di YouTube."""
  return urlparse(url).netloc.removeprefix("www.") in ("youtube.com", "youtu.be")

def is_stream(url: str) -> bool:
  """Indica se il link va gestito da questo modulo invece che dal download diretto."""
  return is_hls(url) or is_youtube(url)


async def hls_duration(client: AsyncClient, url: str) -> float:
  """
  Calcola la durata in secondi di uno stream HLS, sommando i segmenti
  della variante con la qualità più alta.
  """
  playlist = (await client.get(url)).text
  variants = re.findall(r"#EXT-X-STREAM-INF:[^\n]*?BANDWIDTH=(\d+)[^\n]*\n\s*([^\s#][^\n]*)", playlist)
  if variants:
      best = max(variants, key=lambda v: int(v[0]))[1].strip()
      playlist = (await client.get(urljoin(url, best))).text
  return sum(float(d) for d in re.findall(r"#EXTINF:\s*([\d.]+)", playlist))


async def download_hls(url: str, output: Path, headers: Headers, progress: Progress, task_id: TaskID) -> None:
  """
  Scarica uno stream HLS (.m3u8) in un file mp4 tramite ffmpeg, senza ricodificare.
  ffmpeg sceglie automaticamente la qualità migliore disponibile.
  """
  ffmpeg = shutil.which("ffmpeg")
  if ffmpeg is None:
      raise RuntimeError("per scaricare gli stream HLS (.m3u8) è necessario installare ffmpeg")

  # la durata serve solo per stimare la dimensione finale nella barra di avanzamento
  try:
      async with AsyncClient(headers=headers, follow_redirects=True) as client:
          duration = await hls_duration(client, url)
  except Exception:
      duration = 0.0

  process = await asyncio.create_subprocess_exec(
      ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
      "-user_agent", headers.get("User-Agent", "Mozilla/5.0"),
      "-i", url,
      "-c", "copy", "-bsf:a", "aac_adtstoasc", "-f", "mp4",
      "-progress", "pipe:1", "-nostats",
      str(output),
      stdout=asyncio.subprocess.PIPE,
      stderr=asyncio.subprocess.PIPE,
  )

  size, seconds = 0, 0.0
  assert process.stdout is not None
  async for raw in process.stdout:
      key, _, value = raw.decode(errors="ignore").strip().partition("=")
      if key == "total_size" and value.isdigit():
          size = int(value)
      elif key == "out_time_us" and value.isdigit():
          seconds = int(value) / 1_000_000
      elif key == "progress":
          # stima della dimensione finale in base a quanta parte della durata è stata scaricata
          total = size * duration / seconds if duration and seconds else None
          progress.update(task_id, completed=size, total=total)

  _, stderr = await process.communicate()
  if process.returncode != 0:
      output.unlink(missing_ok=True)
      message = stderr.decode(errors="ignore").strip().splitlines()
      raise RuntimeError(f"ffmpeg: {message[-1] if message else f'codice di uscita {process.returncode}'}")
  progress.update(task_id, completed=size, total=size)


async def download_stream(url: str, filename: Path, headers: Headers, progress: Progress, task_id: TaskID, ep_num: str) -> None:
  """
  Scarica l'episodio `ep_num` in `filename`, gestendo file temporaneo,
  messaggi di completamento ed errori come il download diretto.
  """
  temp_filename = filename.with_name(f"{filename.name}.temp")
  try:
      if is_youtube(url):
          raise RuntimeError("gli episodi ospitati su YouTube non possono essere scaricati")
      await download_hls(url, temp_filename, headers, progress, task_id)
      temp_filename.rename(filename)
      progress.update(task_id, description=f"[success]Ep. {ep_num} (Completato)[/]")
  except Exception as e:
      progress.console.print(f"[error]Errore download Ep. {ep_num}: {e}[/]")
