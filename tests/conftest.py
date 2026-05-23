import os
import time
import json
import pytest
from pathlib import Path
from aw_cli.providers.animeworld import Animeworld
from aw_cli.providers.animeunity import Animeunity

# Le fixtures sono considerate deprecate/scadute dopo 7 giorni
DEPRECATION_PERIOD_SECONDS = 7 * 24 * 60 * 60  # 7 giorni

def update_fixtures():
    """Scarica e aggiorna tutte le fixtures per i test unitari in modo rispettoso (con delay)."""
    aw = Animeworld()
    au = Animeunity()

    fixtures_dir = Path(__file__).parent / "fixtures"
    fixtures_dir.mkdir(exist_ok=True)

    def respectful_sleep():
        time.sleep(.5)

    print("Scaricando la pagina latest per AnimeWorld...")
    html_aw_latest = aw._get_html(aw.BASE_URL)
    (fixtures_dir / "aw_latest.html").write_text(html_aw_latest, encoding="utf-8")
    respectful_sleep()

    print("Scaricando la pagina info per un anime di AnimeWorld (Naruto)...")
    html_aw_info = aw._get_html(aw.BASE_URL + "/play/naruto.glnZ0")
    (fixtures_dir / "aw_info.html").write_text(html_aw_info, encoding="utf-8")
    respectful_sleep()

    print("Scaricando il video player player embed per AnimeWorld (p5uzx)...")
    html_aw_player = aw._get_html(aw.BASE_URL + "/api/episode/serverPlayerAnimeWorld?id=p5uzx")
    (fixtures_dir / "aw_player_api.html").write_text(html_aw_player, encoding="utf-8")
    respectful_sleep()

    print("Scaricando i risultati di ricerca API JSON per AnimeWorld...")
    if "csrf-token" not in aw.Client.headers:
        aw._get_html(aw.BASE_URL)
        respectful_sleep()
    response_aw_api_search = aw.Client.post(
        f"{aw.BASE_URL}/api/search/v2",
        params={"keyword": "naruto"}
    )
    if response_aw_api_search.status_code == 200:
        (fixtures_dir / "aw_search_api.json").write_text(
            json.dumps(response_aw_api_search.json(), indent=2), encoding="utf-8"
        )
    respectful_sleep()

    print("Scaricando i risultati di ricerca JSON per AnimeUnity...")
    _ = au._session  # Inizializza sessione/cookies
    respectful_sleep()
    response = au.Client.post(f"{au.BASE_URL}/livesearch", data={"title": "naruto"})
    (fixtures_dir / "au_search.json").write_text(json.dumps(response.json(), indent=2), encoding="utf-8")
    respectful_sleep()

    print("Scaricando la landing page (latest) per AnimeUnity...")
    (fixtures_dir / "au_latest.html").write_text(au._session, encoding="utf-8")
    respectful_sleep()

    print("Scaricando i dati info JSON per un anime di AnimeUnity (id 1469 - Naruto)...")
    response_au_info = au.Client.get(f"{au.BASE_URL}/info_api/1469/")
    (fixtures_dir / "au_info.json").write_text(json.dumps(response_au_info.json(), indent=2), encoding="utf-8")

    print("✓ Tutte le fixtures salvate con successo nella cartella:", fixtures_dir.resolve())


def pytest_addoption(parser):
    parser.addoption(
        "--update-fixtures",
        action="store_true",
        default=False,
        help="Forza la rigenerazione di tutte le fixtures per i test",
    )


@pytest.fixture(scope="session", autouse=True)
def ensure_fixtures(request):
    force_update = request.config.getoption("--update-fixtures")
    fixtures_dir = Path(__file__).parent / "fixtures"
    required_files = [
        "aw_latest.html",
        "aw_info.html",
        "aw_player_api.html",
        "aw_search_api.json",
        "au_search.json",
        "au_latest.html",
        "au_info.json",
    ]

    missing = False
    deprecated = False
    now = time.time()

    if not fixtures_dir.exists():
        missing = True
    else:
        for filename in required_files:
            file_path = fixtures_dir / filename
            if not file_path.exists():
                missing = True
                break

            # Verifica se la fixture è deprecata (più vecchia di 7 giorni)
            file_mtime = file_path.stat().st_mtime
            if now - file_mtime > DEPRECATION_PERIOD_SECONDS:
                deprecated = True

    if force_update or missing or deprecated:
        if force_update:
            reason = "richiesta forzata tramite --update-fixtures"
        else:
            reason = "mancanti" if missing else "deprecate (più vecchie di 7 giorni)"

        import warnings
        warnings.warn(
            UserWarning(f"\n[Pytest] Le fixtures sono {reason}. Avvio autorigenerazione...")
        )
        try:
            update_fixtures()
        except Exception as e:
            warnings.warn(UserWarning(f"Errore durante l'aggiornamento delle fixtures: {e}"))


if __name__ == "__main__":
    update_fixtures()
