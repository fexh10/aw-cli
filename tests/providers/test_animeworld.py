import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from aw_cli.providers.animeworld import Animeworld
from aw_cli.anime import Anime

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


class TestAnimeworld:
    """Test unitari per il provider AnimeWorld usando le fixtures aggiornabili dinamicamente."""

    @pytest.fixture
    def aw(self):
        mock_client = MagicMock()
        return Animeworld(client=mock_client)

    def test_animeworld_search(self, aw):
        import json

        search_json = json.loads(
            (FIXTURES_DIR / "aw_search_api.json").read_text(encoding="utf-8")
        )

        with patch.object(aw, "Client") as mock_client:
            mock_client.post.return_value.json.return_value = search_json
            mock_client.post.return_value.raise_for_status = lambda: None

            animes = aw._search("naruto")
            assert len(animes) > 0, "Nessun anime trovato nella fixture per la ricerca"
            assert animes[0].name != ""
            assert "play/" in animes[0].ref

            # Verify pre-populated metadata
            assert animes[0].anilist_id == 97938
            assert animes[0].info["Stato"] == "Finito"
            assert animes[0].info["Studio"] == "Studio Pierrot"
            assert "Arti Marziali" in animes[0].info["Genere"]
            assert animes[0].info["Trama"] != ""

    def test_animeworld_latest(self, aw):
        html = (FIXTURES_DIR / "aw_latest.html").read_text(encoding="utf-8")

        with patch.object(aw, "_get_html", return_value=html):
            animes = aw._latest("a", specials=False)
            assert len(animes) > 0, "Nessun anime trovato nella fixture per il latest"
            assert animes[0].name != ""
            # The latest episode parsed must be a raw alphanumeric ID (not purely numeric)
            for anime in animes:
                if anime.curr_ep and anime.has_episode(anime.curr_ep):
                    assert not anime.episode(anime.curr_ep).ref.isdigit()

    def test_animeworld_episodes(self, aw):
        html = (FIXTURES_DIR / "aw_info.html").read_text(encoding="utf-8")

        anime = Anime("Naruto", "https://www.animeworld.ac/play/naruto.glnZ0")

        with patch.object(aw, "_get_html", return_value=html):
            episodes = aw._episodes(anime)
            assert len(episodes) > 0
            assert "1" in episodes
            assert not episodes["1"].isdigit()

    def test_animeworld_episode_link(self, aw):
        # We load our new fixture for the player page
        player_html = (FIXTURES_DIR / "aw_player_api.html").read_text(encoding="utf-8")
        anime = Anime("Naruto", "https://www.animeworld.ac/play/naruto.glnZ0")
        episode = Anime.Episode(anime, "1", ref="p5uzx")

        # Mock client get to return response containing player HTML
        mock_response = MagicMock()
        mock_response.text = player_html
        mock_response.status_code = 200
        aw.Client.get.return_value = mock_response

        video_url = aw._episode_link(anime, episode)
        assert (
            video_url
            == "https://srv23-abbaia.sweetpixel.org/DDL/ANIME/Naruto/Naruto_Ep_001_SUB_ITA.mp4"
        )


    def test_animeworld_info_anime(self, aw):
        html = (FIXTURES_DIR / "aw_info.html").read_text(encoding="utf-8")
        anime = Anime("Naruto", "https://www.animeworld.ac/play/naruto.glnZ0")

        with patch.object(aw, "_get_html", return_value=html):
            aw._info_anime(anime)
            assert anime.anilist_id == 20
            assert "Trama" in anime.info
