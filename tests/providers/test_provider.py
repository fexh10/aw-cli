import pytest
from unittest.mock import MagicMock
from aw_cli.providers import create_provider, PROVIDERS_AVAILABLE


class TestProviderFactory:
    """Test unitari per la classe base Provider e la Factory."""

    @pytest.mark.parametrize("provider_name", list(PROVIDERS_AVAILABLE.keys()))
    def test_create_provider_dynamic(self, provider_name):
        """Verifica la creazione dinamica di tutti i provider disponibili."""
        provider = create_provider(provider_name)
        assert provider.__class__.__name__.lower() == provider_name.replace("-", "")

    def test_create_provider_invalid(self):
        """Verifica che venga sollevato un errore per provider non validi."""
        with pytest.raises(ValueError, match="Provider 'invalid' non disponibile"):
            create_provider("invalid")

    @pytest.mark.parametrize("provider_name", list(PROVIDERS_AVAILABLE.keys()))
    def test_client_injection_dynamic(self, provider_name):
        """Verifica che il client venga iniettato correttamente in tutti i provider."""
        mock_client = MagicMock()
        import importlib

        mod_name, cls_name = PROVIDERS_AVAILABLE[provider_name]
        cls = getattr(importlib.import_module(mod_name), cls_name)

        provider = cls(client=mock_client)
        assert provider.Client is mock_client

    @pytest.mark.parametrize("provider_name", list(PROVIDERS_AVAILABLE.keys()))
    def test_client_default_dynamic(self, provider_name):
        """Verifica che venga creato un client di default per tutti i provider."""
        import importlib

        mod_name, cls_name = PROVIDERS_AVAILABLE[provider_name]
        cls = getattr(importlib.import_module(mod_name), cls_name)

        provider = cls()
        assert provider.Client is not None
        assert provider.Client.headers["User-Agent"] is not None
