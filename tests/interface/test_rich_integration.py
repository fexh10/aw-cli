from rich.console import Console
from aw_cli.anime import Anime, AnimeStatus

def test_anime_rich_protocol():
    """Test that Anime class implements __rich_console__ correctly."""
    anime = Anime(name="Test Anime", ref="ref", status=AnimeStatus.ONGOING)
    anime.set_info(
        anilist_id=123,
        status=AnimeStatus.ONGOING,
        info={"Genere": "Action", "Episodi": "12", "Trama": "Test plot"}
    )

    console = Console(file=None)
    with console.capture() as capture:
        console.print(anime)

    output = capture.get()

    assert "Test Anime" in output
    assert "Genere" in output
    assert "Action" in output
    assert "Episodi" in output
    assert "12" in output
    assert "Stato" in output
    assert "In corso" in output
    assert "Trama" in output
    assert "Test plot" in output
