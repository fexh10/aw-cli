import io
from unittest.mock import patch, MagicMock
import pytest

from aw_cli.fzf import Fzf


@pytest.fixture
def fzf():
    """Istanza fittizia (mockata) Fzf bypassando il costruttore reale."""
    with patch.object(Fzf, "__init__", return_value=None):
        instance = Fzf()
        instance._port = 12345
        return instance

class TestBuildCmd:
    """Verifica sinteticamente che _build_cmd configuri le opzioni essenziali."""

    def test_build_cmd_correctness(self, fzf: Fzf):
        cmd = fzf._build_cmd(elements=["a", "b", "c"], prompt="Scegli: ", multi=True)

        assert "--listen" in cmd and "12345" in cmd
        assert "--prompt=Scegli: " in cmd
        assert "--multi" in cmd
        assert "--height=5" in cmd
        assert "--tac" in cmd

    def test_build_cmd_with_filter(self, fzf: Fzf):
        cmd = fzf._build_cmd(elements=["a", "b"], prompt="> ", multi=False, filter=True)
        assert "--phony" in cmd

        # Verifica bind per il reload su filter
        binds = [c for c in cmd if c.startswith("change:reload(")]
        assert len(binds) == 1
        assert "aw_cli.fzf.fzf" in binds[0]

class TestReload:
    """Verifica l'invio del reload HTTP a fzf --listen."""

    def test_reload_sends_post_to_listen_port(self, fzf: Fzf):
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value.__enter__ = MagicMock()
            mock_urlopen.return_value.__exit__ = MagicMock()
            fzf.reload(["x", "y"])

            mock_urlopen.assert_called_once()
            req = mock_urlopen.call_args[0][0]
            assert req.full_url == "http://localhost:12345"
            assert req.method == "POST"
            assert b"reload(printf" in req.data

    def test_reload_escapes_single_quotes(self, fzf: Fzf):
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value.__enter__ = MagicMock()
            mock_urlopen.return_value.__exit__ = MagicMock()
            fzf.reload(["it's a test"])

            req = mock_urlopen.call_args[0][0]
            # L'apostrofo deve essere escaped per POSIX
            assert b"'" in req.data
            assert b"\\'" in req.data

    def test_reload_ignores_os_error(self, fzf: Fzf):
        """Se fzf non è (ancora) pronto, l'errore deve essere ignorato."""
        with patch("urllib.request.urlopen", side_effect=OSError("refused")):
            # Non deve sollevare eccezioni
            fzf.reload(["a", "b"])



class TestFilterEpisodes:
    """Verifica la logica di filtering degli episodi."""

    @pytest.mark.parametrize(
        "query, episodes, expected",
        [
            ("28", ["28", "29-30", "31-35", "40"], "28"),
            ("29-32", ["28", "29-30", "31-35", "40"], "29-30\n31-35"),
            ("30-", ["28", "29-30", "31-35", "40"], "29-30\n31-35\n40"),
            ("-29", ["28", "29-30", "31-35", "40"], "28\n29-30"),
            ("Special", ["Special Episode 1", "10", "20"], "Special Episode 1"),
            ("", ["1", "2"], "1\n2"),
        ],
        ids=[
            "exact_match",
            "range_overlap",
            "open_range_end",
            "open_range_start",
            "substring",
            "empty_query"
        ]
    )
    def test_filter_variations(self, query, episodes, expected):
        from aw_cli.fzf.fzf import _filter_episodes
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            _filter_episodes(query, str(episodes))
            assert mock_stdout.getvalue().strip() == expected
