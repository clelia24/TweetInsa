import json
import os
import hashlib
import secrets

###### Rajouter test sur email deja urtilisé
###### Chercher user par email?
###### regarder delete


DB_FILE = "database_auth.json"

def _load_db():
    """
    Load la database contenant les users.

    Returns
    -------
    TYPE
        None.

    """
    if not os.path.exists(DB_FILE):
        return {"users": []}
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def _save_db(db):
    """
    Save la database.

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
    if salt is None:
        salt = secrets.token_hex(16)
    hashed = hashlib.sha256((salt + password).encode()).hexdigest()
    return hashed, salt

def add_user(username, email, password):
    db = _load_db()
    if any(u["username"] == username for u in db["users"]):
        raise ValueError("Username already exists")
    hashed, salt = _hash_password(password)
    db["users"].append({
        "username": username,
        "email": email,
        "password_hash": hashed,
        "salt": salt
    })
    _save_db(db)

def get_user(username):
    db = _load_db()
    for u in db["users"]:
        if u["username"] == username:
            return u
    return None

def delete_user(username):
    db = _load_db()
    db["users"] = [u for u in db["users"] if u["username"] != username]
    _save_db(db)

def authenticate(username, password):
    u = get_user(username)
    if not u:
        return False
    hashed, _ = _hash_password(password, u["salt"])
    return hashed == u["password_hash"]


add_user("laura", "souverin@insa-toulouse.fr", "1234")
add_user("anais", "noe-achour@insa-toulouse.fr", "abcd")
add_user("astrid", "portapia@insa-toulouse.fr", "1234abcd")


print(get_user("laura"))

delete_user("laura")

authenticate("laura", "1234")
authenticate("laura", "abcd")

add_user("laura", "souverin@insa-toulouse.fr", "1234")