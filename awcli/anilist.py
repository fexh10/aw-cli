import requests
tokenAnilist = None

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

    #query in base alla scelta del preferito
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
        "idAnime" : id_anilist,
        "status" : status_list,
        "episodio" : ep,
    }
    if voto != 0:
        var["score"] = voto
    header_anilist = {'Authorization': 'Bearer ' + tokenAnilist, 'Content-Type': 'application/json', 'Accept': 'application/json'}
    requests.post('https://graphql.anilist.co',headers=header_anilist,json={'query' : query, 'variables' : var}) 
 

def getAnilistUserId() -> int: 
    """
    Collegamento alle API di AniList per trovare
    l'id dell'utente.

    Args:
        tokenAnilist: il token AniList dell'utente.

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
    user_id = int(risposta.json()["data"]["Viewer"]["id"])

    return user_id


def getAnimePrivateRating(user_id: int, id_anime: int) -> str:
    """
    Collegamento alle API di AniList per trovare
    il voto dato all'anime dall'utente.

    Args:
        user_id (int): l'id dell'utente su AniList.
        id_anime (int): l'id dell'anime su Anilist.

    Returns:
        str: il voto dell'utente sotto forma di stringa.
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

    header_anilist = {'Authorization': 'Bearer ' + tokenAnilist, 'Content-Type': 'application/json', 'Accept': 'application/json'}
    risposta = requests.post('https://graphql.anilist.co',headers=header_anilist,json={'query' : query, 'variables' : var}) 
    voto = str(risposta.json()["data"]["MediaList"]["score"])
    if voto == "0":
        voto = "n.d."
    return voto
