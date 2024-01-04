import requests

tokenAnilist = "tokenAnilist: False"
user_id = 0
ratingAnilist = False
preferitoAnilist = False
dropAnilist = False

class TokenError(Exception):
    pass


def addToAnilistFavourite(id_anilist: int, ep: int, voto: float): 
    """
    Collegamento alle API di AniList per aggiornare
    automaticamente gli anime.

    Args:
        id_anilist (int): l'id dell'anime su AniList.
        ep (int): il numero dell'episodio visualizzato.
        voto (float): il voto dell'anime.
    """

    query = """
        mutation ($idAnime: Int, $status: MediaListStatus, $episodio : Int, $score: Float) {
            SaveMediaListEntry (mediaId: $idAnime, status: $status, progress : $episodio, score: $score) {
                status
                progress
                score
            },
            ToggleFavourite(animeId:$idAnime){
                anime {
                    nodes {
                        id
                    }
                }
            }
        }
        """
    
    var = {
        "idAnime": id_anilist,
        "status": "COMPLETED",
        "episodio": ep,
        "score": voto
    }

    requestModifyAnilist(query, var)


def addToAnilist(id_anilist: int, ep: int, status_list: str, voto: float) -> None:
    """
    Collegamento alle API di AniList per aggiornare
    automaticamente gli anime.

    Args:
        id_anilist (int): l'id dell'anime su AniList.
        ep (int): il numero dell'episodio visualizzato.
        voto (float): il voto dell'anime.
        status_list (str): lo stato dell'anime per l'utente. Se è in corso verrà impostato su "CURRENT", se completato su "COMPLETED".
    """

    query = """
    mutation ($idAnime: Int, $status: MediaListStatus, $episodio : Int, $score: Float) {
        SaveMediaListEntry (mediaId: $idAnime, status: $status, progress : $episodio, score: $score) {
            status
            progress
            score
        }
    }
    """

    var = {
        "idAnime": id_anilist,
        "status": status_list,
        "episodio": ep,
    }
    
    if voto != 0:
        var["score"] = voto

    requestModifyAnilist(query, var)
 

def getAnilistUserId() -> int:
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

    header_anilist = {'Authorization': 'Bearer ' + tokenAnilist, 'Content-Type': 'application/json', 'Accept': 'application/json'}
    risposta = requests.post('https://graphql.anilist.co',headers=header_anilist,json={'query' : query})
    if risposta.status_code != 200:
        raise TokenError("Errore: Token AniList sbagliato")

    user_id = int(risposta.json()["data"]["Viewer"]["id"])

    return user_id


def getAnimePrivateRating(id_anime: int) -> int:
    """
    Collegamento alle API di AniList per trovare
    il voto dato all'anime dall'utente.

    Args:
        id_anime (int): l'id dell'anime su Anilist.

    Returns:
        int: il voto dell'utente.
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
        'Authorization': 'Bearer ' + tokenAnilist,
        'Content-Type': 'application/json', 'Accept': 'application/json'
    }
    
    risposta = requests.post('https://graphql.anilist.co',headers=header_anilist, json={'query': query, 'variables': var})
    if risposta.status_code != 200:
        return 0
    
    return str(risposta.json()["data"]["MediaList"]["score"])


def requestModifyAnilist(query: str, var: dict):
    """
    Request alle API di Anilist. 
    Se la richiesta non va a buon fine, viene stampato un errore.

    Args: 
        query (str): la stringa che contiene la query.
        var (dict): dizionario che contiene le variabili da passare alla query.
    """

    header_anilist = {'Authorization': 'Bearer ' + tokenAnilist, 'Content-Type': 'application/json', 'Accept': 'application/json'}
    risposta = requests.post('https://graphql.anilist.co',headers=header_anilist,json={'query' : query, 'variables' : var})
    
    if risposta.status_code != 200:
        print("Impossibile aggiornare AniList!")