import pytest
import json
from unittest.mock import patch
from pathlib import Path
from aw_cli.providers.animeunity import Animeunity

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"

class TestAnimeunity:
    """Test unitari per il provider AnimeUnity usando le fixtures aggiornabili dinamicamente."""

    @pytest.fixture
    def au(self):
        with patch.object(Animeunity, '_get_token', return_value=None):
            return Animeunity()

    def test_animeunity_search(self, au):
        data = json.loads((FIXTURES_DIR / "au_search.json").read_text(encoding="utf-8"))

        with patch.object(au, 'Client') as mock_client:
            mock_client.post.return_value.json.return_value = data
            mock_client.post.return_value.raise_for_status = lambda: None

            animes = au._search("naruto")
            assert len(animes) > 0, "Nessun anime trovato nella fixture per la ricerca"
            assert animes[0].name != ""
            assert "Cover" in animes[0].info
            assert animes[0].info["Cover"].startswith("http")

    def test_animeunity_latest(self, au):
        html = (FIXTURES_DIR / "au_latest.html").read_text(encoding="utf-8")
        au.html = html

        animes = au._latest("a", specials=False)
        assert len(animes) > 0, "Nessun anime trovato nella fixture per il latest"
        assert animes[0].name != ""
        assert "Cover" in animes[0].info
        assert animes[0].info["Cover"].startswith("http")

    def test_animeunity_info_anime(self, au):
        with patch.object(Animeunity, '_get_token', return_value=None):
            au = Animeunity()
        data = json.loads((FIXTURES_DIR / "au_info.json").read_text(encoding="utf-8"))
        from aw_cli.anime import Anime
        anime = Anime("Naruto", "1469")

        with patch.object(au, 'Client') as mock_client:
            mock_client.get.return_value.json.return_value = data
            mock_client.get.return_value.raise_for_status = lambda: None

            au._info_anime(anime)
            assert anime.last_ep == "220"
            assert "Genere" in anime.info
            assert "Action" in anime.info["Genere"]
