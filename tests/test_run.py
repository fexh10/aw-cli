import pytest
from awcli.run import anime, scegliEpisodi
from unittest.mock import patch, Mock

anime.name = "Mushishi"
anime.ep = 26

@pytest.mark.parametrize("input_values,expected", [
    (["0", "27", "1"], (1, 1)),
    (["3-2","3-27", "3-26"], (3, 26)),
    (["", "4"], (1, 26))
])
@patch("builtins.input")
def test_scegliEpisodi(input_mock, input_values, expected):
    input_mock.side_effect = input_values
    result = scegliEpisodi()
    assert result == expected

