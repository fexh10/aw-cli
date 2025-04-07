import requests

class TokenError(Exception):
    pass

def updateAnilist(token, id_anilist: int, ep: int, status_list: str, score: float, favourite: bool = False) -> None:
    """
    Collegamento alle API di AniList per aggiornare lo stato dell'anime

    Args:
        id_anilist (int): l'id dell'anime su AniList.
        ep (int): il numero dell'episodio visualizzato.
        voto (float): il voto dell'anime.
        status_list (str): lo stato dell'anime per l'utente. Se è in corso verrà impostato su "CURRENT", se completato su "COMPLETED".
        favourite (bool): se True, aggiunge l'anime ai preferiti.
    """
    query = """
    mutation ($idAnime: Int, $status: MediaListStatus, $episode : Int, $score: Float) {
        SaveMediaListEntry (mediaId: $idAnime, status: $status, progress : $episode, score: $score) {
            status
            progress
            score
        },""" + ("""
        ToggleFavourite(animeId:$idAnime){
            anime {
                nodes {
                    id
                }
            }
        }""" if favourite else "") + """
    }
    """

    var = {
        "idAnime": id_anilist,
        "status": status_list,
        "episode": ep,
    }
    
    if score != 0:
        var["score"] = score

    requestModifyAnilist(token, query, var)
 

def getAnilistUserId(token) -> int:
    """
    Collegamento alle API di AniList per trovare
    l'id dell'utente in base al token AniList dell'utente.

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

    header_anilist = {'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json', 'Accept': 'application/json'}
    risposta = requests.post('https://graphql.anilist.co',headers=header_anilist,json={'query' : query})
    if risposta.status_code != 200:
        raise TokenError("Errore: Token AniList sbagliato")

    user_id = int(risposta.json()["data"]["Viewer"]["id"])

    return user_id


def getAnimePrivateRating(token, user_id, id_anime: int) -> float:
    """
    Collegamento alle API di AniList per trovare
    il voto dato all'anime dall'utente.

    Args:
        id_anime (int): l'id dell'anime su Anilist.

    Returns:
        float: il voto dell'utente.
    """

    query = """
    query ($idAnime: Int, $userId: Int) {
        MediaList(userId: $userId, mediaId: $idAnime) {
            score
        }
    }
    """
    var = {
        "idAnime": id_anime,
        "userId": user_id
    }

    header_anilist = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json', 'Accept': 'application/json'
    }
    
    risposta = requests.post('https://graphql.anilist.co',headers=header_anilist, json={'query': query, 'variables': var})
    if risposta.status_code != 200:
        return None
    
    return float(risposta.json()["data"]["MediaList"]["score"])


def requestModifyAnilist(token, query: str, var: dict):
    """
    Request alle API di Anilist. 
    Se la richiesta non va a buon fine, viene stampato un errore.

    Args: 
        query (str): la stringa che contiene la query.
        var (dict): dizionario che contiene le variabili da passare alla query.
    """

    header_anilist = {'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json', 'Accept': 'application/json'}
    risposta = requests.post('https://graphql.anilist.co',headers=header_anilist,json={'query' : query, 'variables' : var})
    
    if risposta.status_code != 200:
        print("Impossibile aggiornare AniList!")