import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from aw_cli.providers.animeunity import Animeunity
from aw_cli.anime import Anime

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


class TestAnimeunity:
    """Test unitari per il provider AnimeUnity usando le fixtures aggiornabili dinamicamente."""

    @pytest.fixture
    def au(self):
        mock_client = MagicMock()
        provider = Animeunity(client=mock_client)
        setattr(provider, "_session", "<html></html>")
        return provider

    def test_animeunity_search(self, au):
        data = json.loads((FIXTURES_DIR / "au_search.json").read_text(encoding="utf-8"))

        with patch.object(au, "Client") as mock_client:
            mock_client.post.return_value.json.return_value = data
            mock_client.post.return_value.raise_for_status = lambda: None

            animes = au._search("naruto")
            assert len(animes) > 0, "Nessun anime trovato nella fixture per la ricerca"
            assert animes[0].name != ""

    def test_animeunity_latest(self, au):
        html = (FIXTURES_DIR / "au_latest.html").read_text(encoding="utf-8")
        setattr(au, "_session", html)

        animes = au._latest("a", specials=False)
        assert len(animes) > 0, "Nessun anime trovato nella fixture per il latest"
        assert animes[0].name != ""
        for anime in animes:
            if anime.curr_ep and anime.has_episode(anime.curr_ep):
                assert anime.episode(anime.curr_ep).ref.isdigit()

    def test_animeunity_episodes(self, au):
        anime = Anime("Naruto", "1469", last_ep="2")
        anime.info["Episodi"] = "2"
        mocked_episodes = {
            "episodes": [
                {"number": 1, "id": 12345},
                {"number": 2, "id": 12346}
            ]
        }

        with patch.object(au, "Client") as mock_client:
            mock_client.get.return_value.json.return_value = mocked_episodes
            mock_client.get.return_value.raise_for_status = lambda: None

            episodes = au._episodes(anime)
            assert len(episodes) == 2
            assert episodes["1"] == "12345"
            assert episodes["2"] == "12346"

    def test_animeunity_episode_link(self, au):
        anime = Anime("Naruto", "1469")
        episode = Anime.Episode(anime, "1", ref="12345")

        with patch.object(au, "Client") as mock_client:
            mock_client.get.return_value.text = "window.downloadUrl = 'https://source-video.mp4';"
            mock_client.get.return_value.raise_for_status = lambda: None

            video_url = au._episode_link(anime, episode)
            assert video_url == "https://source-video.mp4"
            # Verify that it passed raw "12345" to the embed API
            # First call is to embed-url/12345
            args, _ = mock_client.get.call_args_list[0]
            assert "embed-url/12345" in args[0]


    def test_animeunity_info_anime(self, au):
        data = json.loads((FIXTURES_DIR / "au_info.json").read_text(encoding="utf-8"))

        anime = Anime("Naruto", "1469")

        with patch.object(au, "Client") as mock_client:
            mock_client.get.return_value.json.return_value = data
            mock_client.get.return_value.raise_for_status = lambda: None

            au._info_anime(anime)
            assert anime.last_ep == "220"
            assert "Genere" in anime.info
            assert "Action" in anime.info["Genere"]
