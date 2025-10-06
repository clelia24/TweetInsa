#------------ Variables globales ------------#

DB_FILE
    #chemin de la DB

NB_USERS
    #Compteur utilisateurs


#------------ Exception ------------#
class UsernameExistsError(Exception)
    #Levée quand essai de création de compte avec un nom d'utilisateur déjà existant

class EmailExistsError(Exception)
    #Levée quand essai de création de compte avec un email déjà utilisé

class UserNotFoundError(Exception)
    #Levée quand essai de suppression d'un utilisateur non existant




#------------ Fonctions publiques ------------#
def test_username(username)
    #Vérifie si le username est dèjà utilisé.


def test_email(email)
    #Vérifie si le username est dèjà utilisé.


def add_user(username, email, password)
    #Ajoute un utilisateur (compte) à la DB.

def get_user(username)
    #Chercher un utilisateur par son nom d'utilisateur.

def get_user_by_email(email)
    #Chercher un utilisateur par son email.

def delete_user(username)
    #Supprime l'utilisateur.

def authenticate(username, password)
    #Authentification par le mot de passe.

def count_users()
    #Renvoie le nombre d'utilisateurs.
