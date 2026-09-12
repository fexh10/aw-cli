import base64
import pytest
from pathlib import Path
from unittest.mock import MagicMock
from aw_cli.providers.animesaturn import Animesaturn
from aw_cli.anime import Anime, AnimeStatus

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


def encode(text: str, key: str) -> str:
    """Operazione inversa di Animesaturn._decode: XOR con la chiave + base64."""
    return base64.b64encode(bytes(ord(c) ^ ord(key[i % len(key)]) for i, c in enumerate(text))).decode()


def mock_response(text: str = "", json_data: dict | None = None) -> MagicMock:
    response = MagicMock()
    response.text = text
    response.json.return_value = json_data
    response.raise_for_status = lambda: None
    return response


class TestAnimesaturn:
    """Test unitari per il provider AnimeSaturn usando le fixtures aggiornabili dinamicamente."""

    @pytest.fixture
    def as_(self):
        return Animesaturn(client=MagicMock())

    def load(self, as_, filename: str):
        """Fa restituire al client mockato il contenuto della fixture."""
        text = (FIXTURES_DIR / filename).read_text(encoding="utf-8")
        as_.Client.get.return_value = mock_response(text)

    def test_animesaturn_search(self, as_):
        self.load(as_, "as_search.html")

        animes = as_._search("naruto")
        assert len(animes) > 0, "Nessun anime trovato nella fixture per la ricerca"

        refs = {anime.ref: anime for anime in animes}
        assert "naruto-iN621" in refs
        assert refs["naruto-iN621"].last_ep == "220"
        # le card delle sezioni laterali non devono finire tra i risultati
        assert all("naruto" in anime.name.lower() for anime in animes)
        # le versioni doppiate vengono riconosciute dal nome
        assert any(anime.dub for anime in animes)

    @staticmethod
    def search_page(slugs: list[str], next_page: str | None) -> str:
        cards = "".join(
            f'<a href="/anime/{slug}" class="ac group"><h3 class="ac__title">{slug}</h3>'
            f'<p class="ac__sub">2020 &middot; 12 ep</p></a>'
            for slug in slugs
        )
        nav = f'<a href="{next_page}" class="page-num" rel="next" aria-label="Successivo"></a>' if next_page else ""
        return cards + nav

    def test_animesaturn_search_pagination(self, as_):
        as_.Client.get.side_effect = [
            mock_response(self.search_page(["a-11111", "b-22222"], "/filter/2?key=x")),
            mock_response(self.search_page(["b-22222", "c-33333"], None)),
        ]

        animes = as_._search("x")
        assert [anime.ref for anime in animes] == ["a-11111", "b-22222", "c-33333"]
        assert as_.Client.get.call_count == 2
        assert as_.Client.get.call_args_list[1].args[0] == f"{as_.BASE_URL}/filter/2?key=x"

    def test_animesaturn_search_max_pages(self, as_):
        pages = [
            mock_response(self.search_page([f"anime-{n}"], f"/filter/{n + 1}?key=x"))
            for n in range(1, 10)
        ]
        as_.Client.get.side_effect = pages

        animes = as_._search("x")
        assert as_.Client.get.call_count == Animesaturn.MAX_SEARCH_PAGES
        assert len(animes) == Animesaturn.MAX_SEARCH_PAGES

    def test_animesaturn_latest(self, as_):
        self.load(as_, "as_latest.xml")

        all_animes = as_._latest("a", specials=True)
        assert len(all_animes) > 0, "Nessun anime trovato nella fixture per il latest"
        for anime in all_animes:
            assert anime.name != ""
            assert anime.has_episode(anime.curr_ep)
            assert f"/anime/{anime.ref}/ep-" in anime.episode(anime.curr_ep).ref

        dub = as_._latest("d", specials=True)
        sub = as_._latest("s", specials=True)
        assert all(anime.dub for anime in dub)
        assert not any(anime.dub for anime in sub)
        assert len(dub) + len(sub) == len(all_animes)

    def test_animesaturn_episodes(self, as_):
        self.load(as_, "as_anime.html")

        episodes = as_._episodes(Anime("Naruto", "naruto-iN621"))
        assert len(episodes) == 220
        assert list(episodes)[:3] == ["1", "2", "3"], "Gli episodi devono essere ordinati per numero"
        assert episodes["1"] == f"{as_.BASE_URL}/anime/naruto-iN621/ep-1"

    def test_animesaturn_info_anime(self, as_):
        self.load(as_, "as_anime.html")

        anime = Anime("Naruto", "naruto-iN621")
        as_._info_anime(anime)
        assert anime.anilist_id == 20
        assert anime.dub is False
        assert anime.status == AnimeStatus.FINISHED
        assert anime.info["Episodi"] == "220"
        assert anime.info["Studio"] == "Studio Pierrot"
        assert "Azione" in anime.info["Genere"]
        assert anime.info["Trama"].startswith("Naruto Uzumaki")
        assert "<" not in "".join(anime.info.values()), "Nei valori non devono restare tag HTML"

    @pytest.mark.parametrize(
        "source, expected",
        [
            ("https://srv1.example.org/_t/1/abc/DDL/ANIME/Naruto/001/playlist.m3u8",
             "https://srv1.example.org/_t/1/abc/DDL/ANIME/Naruto/001/playlist.m3u8"),
            ("youtube/dQw4w9WgXcQ", "https://www.youtube.com/watch?v=dQw4w9WgXcQ"),
        ],
    )
    def test_animesaturn_episode_link(self, as_, source, expected):
        # la pagina del player è quella reale, embed e playlist sono simulate
        # perché contengono token che scadono
        watch_html = (FIXTURES_DIR / "as_watch.html").read_text(encoding="utf-8")
        token = "0123456789abcdef0123456789abcdef"
        embed_html = f'<script>window.__E={{i:6084,k:"{token}",e:1789185446}};</script>'
        playlist = {"d": encode(source, token), "p": "", "t": ""}

        as_.Client.get.side_effect = [
            mock_response(watch_html),
            mock_response(embed_html),
            mock_response(json_data=playlist),
        ]

        anime = Anime("Naruto", "naruto-iN621")
        episode = Anime.Episode(anime, "1", ref=f"{as_.BASE_URL}/anime/naruto-iN621/ep-1")
        assert as_._episode_link(anime, episode) == expected

        # la seconda richiesta va all'iframe estratto dalla pagina reale
        embed_url = as_.Client.get.call_args_list[1].args[0]
        assert embed_url.startswith("https://play.saturncdn.net/embed/")
        # la terza richiesta usa id e token presi dalla pagina embed
        playlist_call = as_.Client.get.call_args_list[2]
        assert playlist_call.args[0] == "https://play.saturncdn.net/embed/6084/playlist"
        assert playlist_call.kwargs["params"]["token"] == token

    def test_animesaturn_episode_link_no_iframe(self, as_):
        as_.Client.get.return_value = mock_response("<html>nessun player</html>")
        anime = Anime("Naruto", "naruto-iN621")
        episode = Anime.Episode(anime, "1", ref=f"{as_.BASE_URL}/anime/naruto-iN621/ep-1")
        with pytest.raises(ValueError):
            as_._episode_link(anime, episode)

    @pytest.mark.parametrize(
        "slug, dub",
        [
            ("naruto-iN621", False),
            ("naruto-ita-ZSYWi", True),
            ("naruto-shippuden-ita-PjvU1", True),
            ("digimon-beatbreak-qg3ji", False),
        ],
    )
    def test_animesaturn_is_dub(self, slug, dub):
        assert Animesaturn._is_dub(slug) is dub

    def test_animesaturn_decode(self):
        key = "0123456789abcdef0123456789abcdef"
        text = "https://srv17.example.org/_t/1/abc/playlist.m3u8"
        assert Animesaturn._decode(encode(text, key), key) == text
