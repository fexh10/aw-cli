"""Test per AnimePreview con flusso sincrono (info + immagini via provider)."""
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from aw_cli.anime import Anime, AnimeStatus
from aw_cli.interface.preview import AnimePreview


@pytest.fixture
def provider_mock():
    provider = MagicMock()
    # Mock info_anime to set Trama (simula il caricamento sincrono)
    def fake_info(anime):
        anime.info["Trama"] = "Trama mockata"
    provider.info_anime.side_effect = fake_info
    # cover_image restituisce None di default (nessuna immagine)
    provider.cover_image.return_value = None
    return provider


@pytest.fixture
def fzf_mock():
    return MagicMock()


@pytest.fixture
def animelist():
    a1 = Anime("Anime 1", "ref1")
    a2 = Anime("Anime 2", "ref2")
    return [a1, a2]


class TestAnimePreview:
    def test_always_calls_info_anime_even_if_trama_present(self, provider_mock, fzf_mock, animelist):
        """info_anime viene SEMPRE chiamato (il caching è nel provider, non qui)."""
        animelist[1].info["Trama"] = "Già presente"

        preview = AnimePreview(provider_mock, animelist, fzf_mock)
        res = preview(index=0, width=80)  # index 0 → animelist[-1] → animelist[1]

        # info_anime sovrascrive la Trama, il risultato è quello del mock
        assert "Trama mockata" in res
        provider_mock.info_anime.assert_called_once_with(animelist[1])

    def test_fetches_info_synchronously_if_trama_missing(self, provider_mock, fzf_mock, animelist):
        """Se la Trama manca, info_anime deve essere chiamato in modo sincrono
        e il risultato deve essere visibile immediatamente senza step intermedi."""
        preview = AnimePreview(provider_mock, animelist, fzf_mock)
        res = preview(index=1, width=80)  # index 1 → animelist[0]

        # info_anime deve essere stato chiamato in modo sincrono
        provider_mock.info_anime.assert_called_once_with(animelist[0])
        # La trama deve apparire nella risposta, senza "[Caricamento...]"
        assert "Anime 1" in res
        assert "Trama mockata" in res
        assert "Caricamento" not in res

    @patch('aw_cli.interface.preview.subprocess.run')
    def test_renders_image_from_provider_cover_image(self, mock_run, provider_mock, fzf_mock, animelist, tmp_path):
        """Se il provider restituisce un path immagine, preview deve renderizzarla con chafa."""
        # Preparo un file immagine finto
        img_file = tmp_path / "12345.jpg"
        img_file.write_bytes(b"fake_image")
        provider_mock.cover_image.return_value = img_file

        # Trama già presente per evitare la chiamata info_anime
        animelist[1].info["Trama"] = "Presente"

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = b"sixel_output"
        mock_run.return_value = mock_result

        preview = AnimePreview(provider_mock, animelist, fzf_mock)
        res = preview(index=0, width=80)

        # cover_image deve essere stato chiamato
        provider_mock.cover_image.assert_called_once_with(animelist[1])
        # chafa deve ricevere il path del file
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert str(img_file) in args
        # L'output deve contenere il rendering
        assert "sixel_output" in res

    @patch('aw_cli.interface.preview.subprocess.run')
    def test_image_rendered_once_cached_in_memory(self, mock_run, provider_mock, fzf_mock, animelist, tmp_path):
        """Se l'immagine è già stata renderizzata (cache RAM), non deve chiamare chafa di nuovo."""
        img_file = tmp_path / "12345.jpg"
        img_file.write_bytes(b"fake_image")
        provider_mock.cover_image.return_value = img_file

        animelist[1].info["Trama"] = "Presente"

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = b"sixel_output"
        mock_run.return_value = mock_result

        preview = AnimePreview(provider_mock, animelist, fzf_mock)
        preview(index=0, width=80)
        preview(index=0, width=80)  # Seconda chiamata

        # chafa deve essere chiamato UNA sola volta
        mock_run.assert_called_once()

    def test_no_image_no_crash(self, provider_mock, fzf_mock, animelist):
        """Se cover_image restituisce None, nessun crash e solo testo."""
        animelist[1].info["Trama"] = "Presente"
        provider_mock.cover_image.return_value = None

        preview = AnimePreview(provider_mock, animelist, fzf_mock)
        res = preview(index=0, width=80)

        assert "Trama mockata" in res
        assert "Anime 2" in res

    def test_index_out_of_range_returns_empty(self, provider_mock, fzf_mock, animelist):
        """Un indice fuori range deve restituire stringa vuota."""
        preview = AnimePreview(provider_mock, animelist, fzf_mock)
        res = preview(index=99, width=80)
        assert res == ""
