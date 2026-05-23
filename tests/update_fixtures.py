import json
from pathlib import Path
from aw_cli.providers.animeworld import Animeworld
from aw_cli.providers.animeunity import Animeunity

def update_fixtures():
    aw = Animeworld()
    au = Animeunity()

    fixtures_dir = Path(__file__).parent / "fixtures"
    fixtures_dir.mkdir(exist_ok=True)

    print("Scaricando la pagina latest per AnimeWorld...")
    html_aw_latest = aw._get_html(aw.BASE_URL)
    (fixtures_dir / "aw_latest.html").write_text(html_aw_latest, encoding="utf-8")

    print("Scaricando la pagina info per un anime di AnimeWorld (Naruto)...")
    html_aw_info = aw._get_html(aw.BASE_URL + "/play/naruto.glnZ0")
    (fixtures_dir / "aw_info.html").write_text(html_aw_info, encoding="utf-8")

    print("Scaricando il video player player embed per AnimeWorld (p5uzx)...")
    html_aw_player = aw._get_html(aw.BASE_URL + "/api/episode/serverPlayerAnimeWorld?id=p5uzx")
    (fixtures_dir / "aw_player_api.html").write_text(html_aw_player, encoding="utf-8")

    print("Scaricando i risultati di ricerca API JSON per AnimeWorld...")
    if "csrf-token" not in aw.Client.headers:
        aw._get_html(aw.BASE_URL)
    response_aw_api_search = aw.Client.post(
        f"{aw.BASE_URL}/api/search/v2",
        params={"keyword": "naruto"}
    )
    if response_aw_api_search.status_code == 200:
        (fixtures_dir / "aw_search_api.json").write_text(
            json.dumps(response_aw_api_search.json(), indent=2), encoding="utf-8"
        )

    print("Scaricando i risultati di ricerca JSON per AnimeUnity...")
    _ = au._session
    response = au.Client.post(f"{au.BASE_URL}/livesearch", data={"title": "naruto"})
    (fixtures_dir / "au_search.json").write_text(json.dumps(response.json(), indent=2), encoding="utf-8")

    print("Scaricando la landing page (latest) per AnimeUnity...")
    (fixtures_dir / "au_latest.html").write_text(au._session, encoding="utf-8")

    print("Scaricando i dati info JSON per un anime di AnimeUnity (id 1469 - Naruto)...")
    response_au_info = au.Client.get(f"{au.BASE_URL}/info_api/1469/")
    (fixtures_dir / "au_info.json").write_text(json.dumps(response_au_info.json(), indent=2), encoding="utf-8")

    print("✓ Tutte le fixtures salvate con successo nella cartella:", fixtures_dir.resolve())

if __name__ == "__main__":
    update_fixtures()
