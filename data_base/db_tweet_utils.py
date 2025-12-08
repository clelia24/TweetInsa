import json
import os
import uuid
from datetime import datetime
import random
from data_base import db_auth_utils


############## IDÉES AMÉLIORATIONS ##############
    # Faire une nouvelle ligne dans le dict du user qui fait le tweet : ajouter les tweet_id
    # Backend : fonction d'affichage (regarder commentaire pour date), de saisie du content...
    #   => essayer de tout faire via le tweet_id, ca sera plus simple je pense


# Dossier où se trouve ce fichier Python
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Chemin absolu vers le fichier JSON dans *le même dossier que ce fichier*
DB_FILE = os.path.join(BASE_DIR, "DB_Tweets.json")



# Créer le fichier DB_Tweets.json s'il n'existe pas
if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump({"tweets": []}, f, indent=2)
    print(f"Créé le fichier {DB_FILE}")


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
    return db_auth_utils._load_db()


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
    db_auth_utils._save_db(db)



#------------ Fonctions publiques ------------#
def post_tweet(username, description,media_path=None):
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
        "content": description,
        "media_path": media_path
    }
    db["tweets"].append(tweet)
    _save_tweets(db)

    db_users = _load_users() 
    for user in db_users["users"]:
        if user["username"] == username:
            if "tweets" not in user:
                user["tweets"] = []
            user["tweets"].append(tweet_id)
            _save_users(db_users)
            return tweet
            break
    else:
        raise db_auth_utils.UserNotFoundError(f"Utilisateur '{username}' introuvable.")



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
        if tweet_id in user.get("tweets", []):
            user["tweets"].remove(tweet_id)
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

# === LIKES ===
def like_tweet(tweet_id: str, username: str):
    """Ajoute ou retire un like (toggle)"""
    db = _load_tweets()
    tweet = None
    for t in db["tweets"]:
        if t["tweet_id"] == tweet_id:
            tweet = t
            break
    if not tweet:
        raise TweetNotFound(f"Tweet {tweet_id} introuvable")

    likes = tweet.get("likes", [])
    if username in likes:
        likes.remove(username)   # unlike
    else:
        likes.append(username)   # like

    tweet["likes"] = likes
    _save_tweets(db)

def get_likes_count(tweet_id: str) -> int:
    try:
        tweet = get_tweet(tweet_id)
        return len(tweet.get("likes", []))
    except TweetNotFound:
        return 0

def has_user_liked(tweet_id: str, username: str) -> bool:
    try:
        tweet = get_tweet(tweet_id)
        return username in tweet.get("likes", [])
    except TweetNotFound:
        return False


# === REPLIES (commentaires) ===
def add_reply(tweet_id: str, username: str, content: str, media_path: str = None, reply_to_reply_id: str = None):
    """
    Ajoute une réponse à un tweet existant ou à une réponse.
    Si reply_to_reply_id est fourni, c'est une réponse à une réponse.
    """
    if len(content) > 140:
        raise TweetTooLong()

    db = _load_tweets()
    tweets = db.get("tweets", [])

    for t in tweets:
        if t["tweet_id"] == tweet_id:
            if "replies" not in t:
                t["replies"] = []

            reply = {
                "reply_id": str(uuid.uuid4()),  # ID unique pour chaque réponse
                "username": username,
                "content": content,
                "date": datetime.now().isoformat(),
                "media_path": media_path,
                "reply_to_reply_id": reply_to_reply_id,  # ID de la réponse parente (None si réponse au tweet principal)
                "sub_replies": []  # Pour stocker les réponses à cette réponse
            }
            
            # Si c'est une réponse à une réponse
            if reply_to_reply_id:
                # Trouver la réponse parente et ajouter la sous-réponse
                def add_sub_reply(replies_list):
                    for r in replies_list:
                        if r.get("reply_id") == reply_to_reply_id:
                            if "sub_replies" not in r:
                                r["sub_replies"] = []
                            r["sub_replies"].append(reply)
                            return True
                        # Recherche récursive dans les sous-réponses
                        if r.get("sub_replies") and add_sub_reply(r["sub_replies"]):
                            return True
                    return False
                
                add_sub_reply(t["replies"])
            else:
                # Réponse directe au tweet
                t["replies"].append(reply)
            
            _save_tweets(db)
            return

    raise TweetNotFound()

# =========================================
# SISTÈME DE RETWEET 
# =========================================

def toggle_retweet(tweet_id: str, username: str):
    """
    Fait un retweet ou annule un retweet (toggle).
    Retourne (is_now_retweeted: bool, nouveau_compteur: int)
    """
    db = _load_tweets()
    tweet = None
    
    for t in db["tweets"]:
        if t["tweet_id"] == tweet_id:
            tweet = t
            break
    
    if not tweet:
        raise TweetNotFound(f"Tweet {tweet_id} introuvable")

    # Initialisation si le tweet est ancien
    if "retweets" not in tweet:
        tweet["retweets"] = []                    # liste des usernames qui ont retweeté
    if "retweet_count" not in tweet:
        tweet["retweet_count"] = 0

    if username in tweet["retweets"]:
        # → Annuler le retweet
        tweet["retweets"].remove(username)
        tweet["retweet_count"] -= 1
        is_retweeted = False
    else:
        # → Retweeter
        tweet["retweets"].append(username)
        tweet["retweet_count"] += 1
        is_retweeted = True

    _save_tweets(db)
    return is_retweeted, tweet["retweet_count"]


def has_user_retweeted(tweet_id: str, username: str) -> bool:
    """Pour savoir si l’utilisateur a déjà retweeté (bouton vert dans le template)"""
    try:
        tweet = get_tweet(tweet_id)
        return username in tweet.get("retweets", [])
    except TweetNotFound:
        return False


def get_retweet_count(tweet_id: str) -> int:
    """Nombre de retweets d’un tweet"""
    try:
        tweet = get_tweet(tweet_id)
        return tweet.get("retweet_count", 0)
    except TweetNotFound:
        return 0