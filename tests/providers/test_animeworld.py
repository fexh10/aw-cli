import pytest
from unittest.mock import patch
from pathlib import Path
from aw_cli.providers.animeworld import Animeworld

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"

class TestAnimeworld:
    """Test unitari per il provider AnimeWorld usando le fixtures aggiornabili dinamicamente."""

    @pytest.fixture
    def aw(self):
        return Animeworld()

    def test_animeworld_search(self, aw):
        html = (FIXTURES_DIR / "aw_search.html").read_text(encoding="utf-8")

        with patch.object(aw, '_get_html', return_value=html):
            animes = aw._search("naruto")
            assert len(animes) > 0, "Nessun anime trovato nella fixture per la ricerca"
            assert animes[0].name != ""
            assert "Cover" in animes[0].info
            assert animes[0].info["Cover"].startswith("http")

    def test_animeworld_latest(self, aw):
        html = (FIXTURES_DIR / "aw_latest.html").read_text(encoding="utf-8")

        with patch.object(aw, '_get_html', return_value=html):
            animes = aw._latest("a", specials=False)
            assert len(animes) > 0, "Nessun anime trovato nella fixture per il latest"
            assert animes[0].name != ""
            assert "Cover" in animes[0].info
            assert animes[0].info["Cover"].startswith("http")

    def test_animeworld_episodes(self, aw):
        html = (FIXTURES_DIR / "aw_info.html").read_text(encoding="utf-8")
        from aw_cli.anime import Anime
        anime = Anime("Naruto", "https://www.animeworld.ac/play/naruto.glnZ0")

        with patch.object(aw, '_get_html', return_value=html):
            episodes = aw._episodes(anime)
            assert len(episodes) > 0
            assert "1" in episodes

    def test_animeworld_info_anime(self, aw):
        html = (FIXTURES_DIR / "aw_info.html").read_text(encoding="utf-8")
        from aw_cli.anime import Anime
        anime = Anime("Naruto", "https://www.animeworld.ac/play/naruto.glnZ0")

        with patch.object(aw, '_get_html', return_value=html):
            aw._info_anime(anime)
            assert anime.anilist_id == 20
            assert "Trama" in anime.info
