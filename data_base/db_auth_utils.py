import json
import os
import hashlib
import secrets

############## IDÉES AMÉLIORATIONS ##############
    # Si DB trop grande, faudra réfléchir à comment ne pas la load sur chaque fonction
    # Trouver user pas email => fonction commune avec le search by username?
    # Delete by email? => fonction commune avec delete by username?
    #

#------------ Variables globales ------------#
DB_FILE = "database_auth.json"  #chemin de la DB

NB_USERS = 0 #Compteur utilisateurs

BASE_DIR = os.path.dirname(DB_FILE) #répertoire dans lequel se trouve la db

# Créer le fichier database_auth.json s'il n'existe pas
if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump({"users": []}, f, indent=2)
    print(f"Créé le fichier {DB_FILE}")

# Vérifier les permissions d'écriture
if not os.access(BASE_DIR, os.W_OK):
    print(f"Erreur : Pas de permission d'écriture pour '{BASE_DIR}' !")


#------------ Classes Exception ------------#
class UsernameExistsError(Exception):
    """Levée quand essai de création de compte avec un nom d'utilisateur déjà existant"""
    pass

class EmailExistsError(Exception):
    """Levée quand essai de création de compte avec un email déjà utilisé"""
    pass

class InvalidPasswordError(Exception):
    """Levée quand le mot de passe ne respecte pas les critères"""
    pass

class UserNotFoundError(Exception):
    """Levée quand essai de suppression d'un utilisateur non existant"""
    pass


#------------ Fonctions internes ------------#
def _load_db():
    """
    Charge la database contenant les users.
    Si le fichier n'existe pas, est vide ou corrompu, retourne {"users": []}.

    Returns
    -------
    Dict
        Database des utilisateurs.

    """
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:  # fichier vide
                return {"users": []}
            return json.loads(content)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"users": []}


def _save_db(db):
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

def _hash_password(password, salt=None):
    """
    Hash un mot de passe avec un salt.

    Parameters
    ----------
    password : str
        Le mot de passe en clair à hasher.
    salt : str, optional
        Sel aléatoire utilisé pour sécuriser le hash.
        - Si None (par défaut), un nouveau sel aléatoire est généré.
        - Sinon, on réutilise le sel fourni (utile pour vérifier un mot de passe existant).

    Returns
    -------
    hashed : str
        Le hash hexadécimal du mot de passe concaténé avec le sel.
    salt : str
        Le sel utilisé pour le hachage, permet d'avoir un hash unique pour chaque compte.
    """
    if salt is None:
        salt = secrets.token_hex(16)
    hashed = hashlib.sha256((salt + password).encode()).hexdigest()
    return hashed, salt

def _refresh_count():
    """
    Compte le nombre de comptes dans la DB.

    Returns
    -------
    None.
    """
    global NB_USERS
    NB_USERS = len(_load_db()["users"])
    
_refresh_count()  #On met à jour NB_USERS dès l'importation du module



#------------ Fonctions publiques ------------#

def test_password(password):
    """
    Vérifie si le mot de passe respecte les critères :
    - Au moins 8 caractères
    - Au moins une lettre majuscule
    - Au moins une lettre minuscule
    - Au moins un chiffre
    """
    if len(password) < 8:
        raise InvalidPasswordError("Le mot de passe doit contenir au moins 8 caractères.")
    if not any(c.isupper() for c in password):
        raise InvalidPasswordError("Le mot de passe doit contenir au moins une lettre majuscule.")
    if not any(c.isdigit() for c in password):
        raise InvalidPasswordError("Le mot de passe doit contenir au moins un chiffre.")
    return True

def test_username(username):
    """
    Vérifie si le username est dèjà utilisé.

    Parameters
    ----------
    username : str
        Nom d'utilisateur.

    Raises
    ------
    UsernameExistsError
        Si le username est déjà utilisé.

    Returns
    -------
    bool
        True si username n'est pas déjà utilisé.
    """
    db = _load_db()
    if any(u["username"] == username for u in db["users"]):
        raise UsernameExistsError(f"Nom d'utilisateur '{username}' déjà utilisé!")
    return True

def test_email(email):
    """
    Vérifie si le username est dèjà utilisé.

    Parameters
    ----------
    email : str
        Email pour le compte.

    Raises
    ------
    EmailExistsError
        Si l'email a déjà été utilisé pour créer un autre compte.

    Returns
    -------
    bool
        True si emmail n'est pas  déjà utilisé.
    """
    db = _load_db()
    if any(u["email"] == email for u in db["users"]):
        raise EmailExistsError(f"Email '{email}' déjà utilisé!")
    return True

def add_user(username, email, password):
    """
    Ajoute un utilisateur (compte) à la DB.

    Parameters
    ----------
    username : str
        Nom d'utilisateur.
    email : str
        Email d'inscription.
    password : str
        Mot de passe.

    Raises
    ------
    UsernameExistsError
        Si le username est déjà utilisé.
    EmailExistsError
        Si l'email a déjà été utilisé pour un autre compte.

    Returns
    -------
    None.

    """
    db = _load_db()
    test_username(username)  # Vérifier si le nom d'utilisateur est unique
    test_email(email)  # Vérifier si l'email est unique
    test_password(password)  # Vérifier les critères du mot de passe
    hashed, salt = _hash_password(password)
    db["users"].append({
        "username": username,
        "email": email,
        "password_hash": hashed,
        "salt": salt,
        "tweets": [] #liste des tweets de l'utilisateur
    })
    try:
        _save_db(db)
        _refresh_count()
        print(f"Utilisateur {username} enregistré dans {DB_FILE}")
    except Exception as e:
        print(f"Erreur lors de l'enregistrement de l'utilisateur: {e}")
        raise


def get_user(username):
    """
    Chercher un utilisateur par son nom d'utilisateur.

    Parameters
    ----------
    username : str
        Nom d'utilisateur.

    Returns
    -------
    u : dict
        Infos de l'utilisateur.
    None si inconnu.
    """
    db = _load_db()
    for u in db["users"]:
        if u["username"] == username:
            return u
    return None

def get_user_by_email(email):
    """
    Chercher un utilisateur par son email.

    Parameters
    ----------
    email : str
        Email lié au compte.

    Returns
    -------
    u : dict
        Infos de l'utilisateur.
    None si inconnu.
    """
    db = _load_db()
    for u in db["users"]:
        if u["email"] == email:
            return u
    return None

def delete_user(username):
    """
    Supprime l'utilisateur.

    Parameters
    ----------
    username : str
        Nom d'utilisateur du compte à supprimer.

    Returns
    -------
    None.
    """
    db = _load_db()
    before = len(db["users"])
    db["users"] = [u for u in db["users"] if u["username"] != username]
    after = len(db["users"])
    if after==before:  #Aucun utilisateur supprimé
        raise UserNotFoundError(f"Utilisateur '{username}' introuvable!")
    _save_db(db)
    _refresh_count()

def authenticate(username, password):
    """
    Authentification par le mot de passe.

    Parameters
    ----------
    username : str
        Nom d'utilisateur.
    password : str
        Mot de passe.

    Returns
    -------
    Bool
        TRUE si authentification validée, FALSE sinon.
    """
    u = get_user(username)
    if not u: #Si user n'existe pas
        return False
    hashed, _ = _hash_password(password, u["salt"])
    return hashed == u["password_hash"]

def count_users():
    """
    Renvoie le nombre d'utilisateurs.

    Returns
    -------
    NB_USERS : int
        Nombre de comptes dans la DB.
    """
    return NB_USERS

def add_tweet(username, tweet_content):
    """
    Ajoute un tweet à l'utilisateur.
    """
    db = _load_db()
    for u in db["users"]:
        if u["username"] == username:
            u["tweets"].append({
                "content": tweet_content,
                "date": "2025-10-26"  # À remplacer par la date actuelle plus tard
            })
            _save_db(db)
            return True
    return False

def get_user_tweets(username):
    """
    Récupère les tweets d'un utilisateur.
    """
    u = get_user(username)
    return u["tweets"] if u else []
