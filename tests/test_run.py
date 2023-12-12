import pytest
import awcli.run as run
from awcli.anime import Anime
from unittest.mock import patch, MagicMock


run.anime = Anime("Test", "no_url", 26, 26)

@pytest.mark.parametrize("input_values,expected", [
    (["0", "27", "1"], (1, 1)),
    (["3-2","3-27", "3-26"], (3, 26)),
    (["", "4"], (1, 26))
])
@patch("builtins.input")
def test_scegliEpisodi(input_mock, input_values, expected):
    input_mock.side_effect = input_values
    result = run.scegliEpisodi()
    assert result == expected

