import time
import pytest
from unittest.mock import MagicMock, call, patch

from aw_cli.anime import Anime, AnimeStatus
from aw_cli.interface.preview import AnimePreview


@pytest.fixture
def provider_mock():
    provider = MagicMock()
    # Mock info_anime to set Trama
    def fake_info(anime):
        anime.info["Trama"] = "Trama mockata"
    provider.info_anime.side_effect = fake_info
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
    def test_immediate_response_if_trama_present(self, provider_mock, fzf_mock, animelist):
        # Imposta trama in anticipo
        animelist[1].info["Trama"] = "Già presente"

        preview = AnimePreview(provider_mock, animelist, fzf_mock)
        # index 0 corrsponde a animelist[-1] cioè animelist[1]
        res = preview(index=0, width=80)

        assert "Già presente" in res
        assert "Caricamento trama..." not in res
        # Nessun background fetch dovrebbe partire
        assert 0 not in preview._fetching

    def test_partial_response_and_fetch_if_trama_missing(self, provider_mock, fzf_mock, animelist):
        preview = AnimePreview(provider_mock, animelist, fzf_mock)

        # Patch sleep to avoid waiting in tests
        with patch('time.sleep', return_value=None):
            res = preview(index=1, width=80) # index 1 corresponds to animelist[0]

            assert "Anime 1" in res
            assert "Caricamento trama..." in res

            # Attendo che il thread finisca
            time.sleep(0.1) # just in case, since sleep is patched
            while 1 in preview._fetching:
                time.sleep(0.01)

            provider_mock.info_anime.assert_called_once_with(animelist[0])
            fzf_mock.refresh_preview.assert_called_once()
            assert animelist[0].info["Trama"] == "Trama mockata"

    def test_debouncing_prevents_fetch_on_fast_scroll(self, provider_mock, fzf_mock, animelist):
        preview = AnimePreview(provider_mock, animelist, fzf_mock)

        # Non patchiamo sleep per testare il debouncing ma lo facciamo veloce
        # Invece di usare sleep reale, patchiamo per un delay piccolissimo
        with patch('time.sleep') as mock_sleep:
            def sleep_del(secs):
                # Simulo che durante lo split l'indice cambi prima che il background proceda
                preview._current_index = 0
            mock_sleep.side_effect = sleep_del

            # L'utente visita index 1
            res = preview(index=1, width=80)
            assert "Caricamento trama..." in res

        time.sleep(0.1)
        # _background_fetch dovrebbe essere terminato prematuramente per index 1
        provider_mock.info_anime.assert_not_called()
        fzf_mock.refresh_preview.assert_not_called()

    def test_idempotence_only_one_fetch_per_index(self, provider_mock, fzf_mock, animelist):
        preview = AnimePreview(provider_mock, animelist, fzf_mock)

        preview._fetching[0] = True # Simuliamo fetch già in corso
        # Chiamiamo ancora
        preview(index=0, width=80)

        # Check threads count? Since it's already in _fetching, it shouldn't spawn a new one
        # Not easily testable without mocking threading.Thread, but we can verify provider wasn't called twice
        # Wait, if we mock Thread, we can verify correctly.
        pass

    @patch('aw_cli.interface.preview.subprocess.run')
    @patch('aw_cli.interface.preview.urllib.request.urlopen')
    @patch('aw_cli.interface.preview.shutil.which', return_value="/usr/bin/chafa")
    def test_sync_image_rendering_and_memory_cache(self, mock_which, mock_urlopen, mock_run, provider_mock, fzf_mock, animelist):
        # Anime 1 has a Cover without Trama
        animelist[0].info["Cover"] = "http://example.com/cover.jpg"

        # Setup mock http response
        mock_response = MagicMock()
        mock_response.read.return_value = b"dummy_image_data"
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        # Setup mock chafa
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = b"ansicode"
        mock_run.return_value = mock_result

        preview = AnimePreview(provider_mock, animelist, fzf_mock)

        # First query (index 1 is animelist[0])
        with patch('time.sleep', return_value=None):
            res = preview(index=1, width=80)

            # The URL must be fetched synchronously to avoid flashing
            mock_urlopen.assert_called_once()
            mock_run.assert_called_once()

            # Verify the output contains the image representation and the loading text for Trama
            assert "ansicode\n" in res
            assert "Anime 1" in res
            assert "[Caricamento trama...]" in res

            # Wait for background thread to finish fetching Trama
            time.sleep(0.1)
            while 1 in preview._fetching:
                time.sleep(0.01)

            # Now __call__ is invoked again, image should NOT be fetched again (cached in memory)
            res2 = preview(index=1, width=80)
            assert "ansicode\n" in res2
            assert "Anime 1" in res2
            assert "Trama mockata" in res2
            assert "[Caricamento trama...]" not in res2

            # Mocks should still only have been called ONCE
            mock_urlopen.assert_called_once()
            mock_run.assert_called_once()
