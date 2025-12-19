import httpx

class TokenError(Exception):
    pass

def update_anilist(token: str, anilist_id: int, ep: int, status_list: str, score: float, favourite: bool = False) -> None:
    """
    Collegamento alle API di AniList per aggiornare lo stato dell'anime

    Args:
        anilist_id (int): l'id dell'anime su AniList.
        ep (int): il numero dell'episodio visualizzato.
        status_list (str): lo stato dell'anime per l'utente. Se è in corso verrà impostato su "CURRENT", se completato su "COMPLETED".
        score (float): il voto dell'anime.
        favourite (bool): se True, aggiunge l'anime ai preferiti.
    """
    query = """
    mutation ($anime_id: Int, $status: MediaListStatus, $episode : Int, $score: Float) {
        SaveMediaListEntry (mediaId: $anime_id, status: $status, progress : $episode, score: $score) {
            status
            progress
            score
        },""" + ("""
        ToggleFavourite(animeId:$anime_id){
            anime {
                nodes {
                    id
                }
            }
        }""" if favourite else "") + """
    }
    """

    var = {
        "anime_id": anilist_id,
        "status": status_list,
        "episode": ep,
    }
    
    if score != 0:
        var["score"] = score

    make_anilist_request(token, query, var)
 
def get_user_id(token: str) -> int:
    """
    Collegamento alle API di AniList per trovare
    l'id dell'utente in base al token AniList dell'utente.

    Args:
        token (str): il token AniList dell'utente.

    Returns:
        int: l'id dell'utente.
    """

    query = """
        query {
            Viewer {
                id
            }
        }
    """

    headers = {'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json', 'Accept': 'application/json'}
    response = httpx.post('https://graphql.anilist.co', headers=headers, json={'query': query})
    if response.status_code != 200:
        raise TokenError("Errore: Token AniList sbagliato")

    user_id = int(response.json()["data"]["Viewer"]["id"])

    return user_id

def get_anime_private_rating(token, user_id, anime_id: int) -> (float | None):
    """
    Collegamento alle API di AniList per trovare
    il voto dato all'anime dall'utente.

    Args:
        user_id (int): l'id dell'utente.
        anime_id (int): l'id dell'anime su Anilist.

    Returns:
        float: il voto dell'utente.
    """

    query = """
    query ($anime_id: Int, $user_id: Int) {
        MediaList(userId: $user_id, mediaId: $anime_id) {
            score
        }
    }
    """
    var = {
        "anime_id": anime_id,
        "user_id": user_id
    }

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json', 'Accept': 'application/json'
    }

    response = httpx.post('https://graphql.anilist.co', headers=headers, json={'query': query, 'variables': var})
    if response.status_code != 200:
        return None
    
    return float(response.json()["data"]["MediaList"]["score"])

def make_anilist_request(token: str, query: str, var: dict) -> None:
    """
    Request alle API di Anilist. 
    Se la richiesta non va a buon fine, viene stampato un errore.

    Args: 
        token (str): il token AniList dell'utente.
        query (str): la stringa che contiene la query.
        var (dict): dizionario che contiene le variabili da passare alla query.
    """

    header_anilist = {'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json', 'Accept': 'application/json'}
    risposta = httpx.post('https://graphql.anilist.co', headers=header_anilist, json={'query': query, 'variables': var})

    if risposta.status_code != 200:
        print("Impossibile aggiornare AniList!")