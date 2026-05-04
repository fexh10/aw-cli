import pytest
from aw_cli.providers import create_provider, PROVIDERS_AVAILABLE

class TestProviderFactory:
    """Test unitari per la Factory dei provider."""

    @pytest.mark.parametrize("provider_name", list(PROVIDERS_AVAILABLE.keys()))
    def test_create_provider_dynamic(self, provider_name):
        """Verifica la creazione dinamica di tutti i provider disponibili."""
        provider = create_provider(provider_name)
        assert provider.__class__.__name__.lower() == provider_name

    def test_create_provider_invalid(self):
        """Verifica che venga sollevato un errore per provider non validi."""
        with pytest.raises(ValueError, match="Provider 'invalid' non disponibile"):
            create_provider("invalid")
