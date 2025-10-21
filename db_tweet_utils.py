import json
import os
import uuid
from datetime import datetime
import random
from database.db_auth_utils import UserNotFoundError

############## IDÉES AMÉLIORATIONS ##############
    # Faire une nouvelle ligne dans le dict du user qui fait le tweet : ajouter les tweet_id
    # Backend : fonction d'affichage (regarder commentaire pour date), de saisie du content...
    #   => essayer de tout faire via le tweet_id, ca sera plus simple je pense

#------------ Variables globales ------------#
DB_FILE = "./DB_Tweets.json"  #chemin de la DB
DB_AUTH = "./data_base/database_auth.json"



#------------ Classes Exception ------------#
class TweetTooLong(Exception):
    """Levée quand la taille du tweet dépasse 140 caractères"""
    pass

class TweetNotFound(Exception):
    """Levée quand tweet non trouvé"""
    pass


#------------ Fonctions internes ------------#
def _load_tweets():
    """
    Charge la database contenant les tweets.
    Si le fichier n'existe pas, est vide ou corrompu, retourne {"tweets": []}.

    Returns
    -------
    Dict
        Database des tweets.

    """
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:  # fichier vide
                return {"tweets": []}
            return json.loads(content)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"tweets": []}
    
def _load_users():
    """
    Charge la database contenant les utilisateurs.
    Si le fichier n'existe pas, est vide ou corrompu, retourne {"users": []}.

    Returns
    -------
    Dict
        Database des users.

    """
    try:
        with open(DB_AUTH, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:  # fichier vide
                return {"users": []}
            return json.loads(content)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"users": []}


def _save_tweets(db):
    """
    Sauvegarde la database.

    Parameters
    ----------
    db : dict
        Database à sauver.

    Returns
    -------
    None.
    """
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2)

def _save_users(db):
    """
    Sauvegarde la database.

    Parameters
    ----------
    db : dict
        Database à sauver.

    Returns
    -------
    None.
    """
    with open(DB_AUTH, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2)



#------------ Fonctions publiques ------------#
def post_tweet(username, description):
    """
    Rajoute un tweet à la base de données.

    Parameters
    ----------
    username : str
        Nom d'utilisateur du compte qui tweet.
    description : str
        Ce qui est posté.
        
    Raises
    ------
    TweetTooLong
        Si le tweet dépasse 140 caractères.

    Returns
    -------
    tweet : dict
        Toutes les infos du tweet.
    """
    if len(description) > 140:
        raise TweetTooLong("Tweet trop long!")
    db = _load_tweets()
    tweet_id = str(uuid.uuid4())
    tweet = {
        "tweet_id": tweet_id,
        "username": username,
        "date": datetime.now().isoformat(timespec="seconds"), # strftime("%d/%m/%Y %H:%M") est mieux pour afficher
        "content": description
    }
    db["tweets"].append(tweet)
    _save_tweets(db)

    db_users = _load_users() 
    for user in db_users["users"]:
        if user["username"] == username:
            user["tweets_posted"].append(tweet_id)
            break
    else:
        raise UserNotFoundError(f"Utilisateur '{username}' introuvable.")

    

    #return tweet

def get_id(tweet):
    """
    Donne l'id du tweet

    Parameters
    ----------
    tweet : dict
        Tweet.

    Returns
    -------
    str
        Id unique du tweet.
    """
    return tweet["tweet_id"]

def get_tweet(tweet_id):
    """
    Donne le tweet correspodant a l'id.

    Parameters
    ----------
    tweet_id : str
        Id du tweet à trouver.

    Raises
    ------
    TweetNotFound
        Si l'id ne correspond à aucun tweet.

    Returns
    -------
    t : dict
        Tweet crrespondant.
    """
    db = _load_tweets()
    for t in db["tweets"]:
        if t["tweet_id"] == tweet_id:
            return t
    raise TweetNotFound(f"Tweet ({tweet_id}) introuvable!")
    

def delete_tweet(tweet_id):
    """
    Supprime un tweet.

    Parameters
    ----------
    tweet_id : str
        Id du tweet à supprimer.

    Returns
    -------
    None.
    """
    db = _load_tweets()
    before = len(db["tweets"])
    db["tweets"] = [u for u in db["tweets"] if u["tweet_id"] != tweet_id]
    after = len(db["tweets"])
    if after == before:
        raise TweetNotFound(f"Tweet ({tweet_id}) introuvable!")
    _save_tweets(db)

    # Retirer le tweet_id de l'utilisateur correspondant
    db_users = _load_users()
    for user in db_users["users"]:
        if tweet_id in user.get("tweets_posted", []):
            user["tweets_posted"].remove(tweet_id)
            break
    _save_users(db_users)



def afficher_tweet(tweet_id):
    """
    Affichage d'un tweet.

    Parameters
    ----------
    tweet_id : str
        Id du tweet.

    Returns
    -------
    str
        Username de l'utilisateur qui a posté.
    str
        Date du post.
    str
        Contenu du post.
    """
    t = get_tweet(tweet_id)
    return t["username"], t["date"], t["content"]

def select_random_tweet():
    """
    Pour choisir un tweet aléatoirement dans la DB de tweets.

    Raises
    ------
    TweetNotFound
        Si la DB est vide.

    Returns
    -------
    str
        Id du tweet.
    """
    db = _load_tweets()
    if not db["tweets"]:
        raise TweetNotFound("Aucun tweet dans la base de données.")
    random_tweet = random.choice(db["tweets"])
    return random_tweet["tweet_id"]
    

