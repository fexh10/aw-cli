import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from urllib.parse import parse_qs, urlsplit
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
            assert mock_client.post.call_args.kwargs["url"] == "https://www.animeunity.co/livesearch"

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

    @pytest.mark.parametrize("fhd, expected_h", [(True, ["1"]), (False, None)])
    def test_animeunity_hls_when_download_url_is_empty(self, au, fhd, expected_h):
        anime = Anime("Naruto", "1469")
        episode = Anime.Episode(anime, "1", ref="12345")
        page = """
            window.downloadUrl = '';
            window.masterPlaylist = {
                params: {'token': 'a+b/=', 'expires': '123456', 'asn': ''},
                url: 'https://vixcloud.cc/playlist/987?existing=yes',
            };
        """ + f"window.canPlayFHD = {str(fhd).lower()};"

        with patch.object(au, "Client") as mock_client:
            mock_client.get.side_effect = [
                MagicMock(text="https://vixcloud.cc/embed/987"),
                MagicMock(text=page),
            ]
            link = au._episode_link(anime, episode)

        parts = urlsplit(link)
        assert parts.path == "/playlist/987"
        query = parse_qs(parts.query)
        assert query["token"] == ["a+b/="]
        assert query["expires"] == ["123456"]
        assert query["existing"] == ["yes"]
        assert query.get("h") == expected_h

    def test_animeunity_empty_video_link_has_clear_error(self, au):
        anime = Anime("Naruto", "1469")
        episode = Anime.Episode(anime, "1", ref="12345")
        with patch.object(au, "Client") as mock_client:
            mock_client.get.side_effect = [
                MagicMock(text="https://vixcloud.cc/embed/987"),
                MagicMock(text="window.downloadUrl = '';"),
            ]
            with pytest.raises(ValueError, match="playlist HLS non trovati"):
                au._episode_link(anime, episode)


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
