import requests

tokenAnilist = "tokenAnilist: False"
user_id = 0
ratingAnilist = False
preferitoAnilist = False

class TokenError(Exception):
    pass


def anilistApi(id_anilist: int, ep: int, voto: float, status_list: str, preferiti: bool) -> None:
    """
    Collegamento alle API di AniList per aggiornare
    automaticamente gli anime.

    Args:
        id_anilist (int): l'id dell'anime su AniList.
        ep (int): il numero dell'episodio visualizzato.
        voto (float): il voto dell'anime.
        status_list (str): lo stato dell'anime per l'utente. Se è in corso verrà impostato su "CURRENT", se completato su "COMPLETED".
        preferiti (bool) : True se l'utente ha scelto di mettere l'anime tra i preferiti, altrimenti False.
    """

    # query in base alla scelta del preferito
    if not preferiti:
        query = """
        mutation ($idAnime: Int, $status: MediaListStatus, $episodio : Int, $score: Float) {
            SaveMediaListEntry (mediaId: $idAnime, status: $status, progress : $episodio, score: $score) {
                status
                progress
                score
            }
        }
        """
    else:
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
        "status": status_list,
        "episodio": ep,
    }
    
    if voto != 0:
        var["score"] = voto
    header_anilist = {'Authorization': 'Bearer ' + tokenAnilist, 'Content-Type': 'application/json', 'Accept': 'application/json'}
    risposta = requests.post('https://graphql.anilist.co',headers=header_anilist,json={'query' : query, 'variables' : var})
    if risposta.status_code != 200:
        print("Impossibile aggiornare AniList!")
 

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
