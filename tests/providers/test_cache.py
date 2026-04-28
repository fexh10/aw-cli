import hashlib
import json
import time
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from aw_cli.anime import Anime, AnimeStatus
from aw_cli.providers.provider import Provider


class ConcreteProvider(Provider):
    """Provider concreto minimale per testare la logica di cache nella base class."""
    def __init__(self):
        super().__init__("https://example.com")

    def _search(self, input):
        return []

    def _latest(self, filter, specials):
        return []

    def _episodes(self, anime):
        return {}

    def _episode_link(self, anime, episode):
        return ""

    def _info_anime(self, anime):
        anime.set_info(
            anilist_id=12345,
            status=AnimeStatus.ONGOING,
            info={
                "Categoria": "TV",
                "Audio": "Giapponese",
                "Trama": "Una trama di esempio",
                "Cover": "http://example.com/cover.jpg",
            }
        )


@pytest.fixture
def provider():
    return ConcreteProvider()


@pytest.fixture
def anime():
    a = Anime("Test Anime", "https://example.com/anime/test")
    a.info["Cover"] = "http://example.com/cover.jpg"
    return a


# ── Info Cache ──────────────────────────────────────────────────────────────

class TestInfoCache:
    def test_info_anime_saves_cache_on_first_call(self, provider, anime, tmp_path):
        """Alla prima chiamata, info_anime deve salvare un file JSON in cache."""
        with patch.object(provider, '_get_info_cache_dir', return_value=tmp_path):
            provider.info_anime(anime)

        json_files = list(tmp_path.glob("*.json"))
        assert len(json_files) == 1

        data = json.loads(json_files[0].read_text())
        assert data["anilist_id"] == 12345
        assert data["status"] == "In corso"
        assert data["info"]["Trama"] == "Una trama di esempio"
        assert data["info"]["Cover"] == "http://example.com/cover.jpg"

    def test_info_anime_loads_from_cache_without_network(self, provider, anime, tmp_path):
        """Se il file cache esiste, info_anime NON deve chiamare _info_anime."""
        cache_key = hashlib.md5(anime.ref.encode()).hexdigest()
        cache_file = tmp_path / f"{cache_key}.json"
        cache_data = {
            "anilist_id": 99999,
            "status": "Finito",
            "info": {
                "Categoria": "OVA",
                "Trama": "Trama dalla cache",
                "Cover": "http://example.com/cached.jpg",
            }
        }
        cache_file.write_text(json.dumps(cache_data))

        with patch.object(provider, '_get_info_cache_dir', return_value=tmp_path):
            with patch.object(provider, '_info_anime') as mock_info:
                provider.info_anime(anime)
                mock_info.assert_not_called()

        assert anime.anilist_id == 99999
        assert anime.status == AnimeStatus.FINISHED
        assert anime.info["Trama"] == "Trama dalla cache"

    def test_info_anime_preserves_cover_from_search(self, provider, anime, tmp_path):
        """La Cover ottenuta durante la search deve essere preservata dopo info_anime."""
        with patch.object(provider, '_get_info_cache_dir', return_value=tmp_path):
            provider.info_anime(anime)

        assert "Cover" in anime.info

    @patch('aw_cli.providers.provider.time.time')
    def test_info_anime_saves_cached_at_timestamp(self, mock_time, provider, anime, tmp_path):
        """info_anime deve salvare il timestamp corrente in cached_at."""
        mock_time.return_value = 1000.0
        with patch.object(provider, '_get_info_cache_dir', return_value=tmp_path):
            provider.info_anime(anime)

        json_files = list(tmp_path.glob("*.json"))
        data = json.loads(json_files[0].read_text())
        assert data["cached_at"] == 1000.0

    @pytest.mark.parametrize("status,age_hours,should_fetch", [
        ("In corso", 1.5, True),      # > 1 hour
        ("In corso", 0.5, False),     # < 1 hour
        ("Terminato", 24 * 31, True), # > 30 days
        ("Terminato", 24 * 29, False),# < 30 days
        ("Non rilasciato", 25, True), # > 24 hours
        ("Non rilasciato", 23, False),# < 24 hours
        ("Sconosciuto", 25, True),    # > 24 hours
        ("Sconosciuto", 23, False),   # < 24 hours
    ])
    @patch('aw_cli.providers.provider.time.time')
    def test_info_anime_respects_ttl_based_on_status(self, mock_time, provider, anime, tmp_path, status, age_hours, should_fetch):
        """Verifica la scadenza del TTL in base allo stato dell'anime usando time.time e configurazione di default."""
        cache_key = hashlib.md5(anime.ref.encode()).hexdigest()
        cache_file = tmp_path / f"{cache_key}.json"

        # Simula il file di cache scritto nel passato
        # base time: 1000000.0
        current_time = 1000000.0
        cached_time = current_time - (age_hours * 3600)

        cache_data = {
            "anilist_id": 99999,
            "status": status,
            "cached_at": cached_time,
            "info": {
                "Categoria": "TV",
                "Trama": "Trama dalla cache",
            }
        }
        cache_file.write_text(json.dumps(cache_data))

        # Facciamo finta che utilities abbia queste configurazioni (ci prepariamo per il GREEN)
        mock_config = {
            "cache": {
                "ttl_ongoing_hours": 1,
                "ttl_unreleased_hours": 24,
                "ttl_finished_days": 30
            }
        }

        mock_time.return_value = current_time

        with patch.object(provider, '_get_info_cache_dir', return_value=tmp_path):
            with patch('aw_cli.providers.provider.ut.config_data', mock_config):
                with patch.object(provider, '_info_anime') as mock_info:
                    provider.info_anime(anime)
                    if should_fetch:
                        mock_info.assert_called_once()
                    else:
                        mock_info.assert_not_called()


# ── Image Cache ─────────────────────────────────────────────────────────────

class TestImageCache:
    @patch('aw_cli.providers.provider.urllib.request.urlopen')
    def test_cover_image_saves_to_disk(self, mock_urlopen, provider, anime, tmp_path):
        """cover_image deve scaricare e salvare l'immagine su disco."""
        mock_response = MagicMock()
        mock_response.read.return_value = b"fake_jpg_data"
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        with patch.object(provider, '_get_image_cache_dir', return_value=tmp_path):
            path = provider.cover_image(anime)

        assert path is not None
        assert path.exists()
        assert path.read_bytes() == b"fake_jpg_data"

    @patch('aw_cli.providers.provider.urllib.request.urlopen')
    def test_cover_image_uses_anilist_id_as_filename(self, mock_urlopen, provider, anime, tmp_path):
        """Se anilist_id è presente, il file si chiama {anilist_id}.jpg."""
        anime.anilist_id = 54321

        mock_response = MagicMock()
        mock_response.read.return_value = b"data"
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        with patch.object(provider, '_get_image_cache_dir', return_value=tmp_path):
            path = provider.cover_image(anime)

        assert path.name == "54321.jpg"

    @patch('aw_cli.providers.provider.urllib.request.urlopen')
    def test_cover_image_uses_md5_without_anilist_id(self, mock_urlopen, provider, tmp_path):
        """Senza anilist_id, il nome usa MD5 dell'URL."""
        anime_no_id = Anime("No ID", "ref")
        anime_no_id.info["Cover"] = "http://example.com/other.jpg"

        mock_response = MagicMock()
        mock_response.read.return_value = b"data"
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        with patch.object(provider, '_get_image_cache_dir', return_value=tmp_path):
            path = provider.cover_image(anime_no_id)

        expected = hashlib.md5(b"http://example.com/other.jpg").hexdigest() + ".jpg"
        assert path.name == expected

    def test_cover_image_skips_network_if_cached(self, provider, anime, tmp_path):
        """Se l'immagine è già su disco, NON deve fare richieste di rete."""
        anime.anilist_id = 54321
        cached_file = tmp_path / "54321.jpg"
        cached_file.write_bytes(b"already_cached")

        with patch.object(provider, '_get_image_cache_dir', return_value=tmp_path):
            with patch('aw_cli.providers.provider.urllib.request.urlopen') as mock_urlopen:
                path = provider.cover_image(anime)
                mock_urlopen.assert_not_called()

        assert path == cached_file

    def test_cover_image_returns_none_without_cover_url(self, provider, tmp_path):
        """Senza Cover URL, cover_image deve restituire None."""
        anime_no_cover = Anime("No Cover", "ref")

        with patch.object(provider, '_get_image_cache_dir', return_value=tmp_path):
            path = provider.cover_image(anime_no_cover)

        assert path is None
