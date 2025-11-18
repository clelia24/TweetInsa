import traceback
from flask import Flask, request, render_template, redirect, url_for, session, jsonify, flash
from .db_auth_utils import *
from .db_auth_utils import _load_db,_save_db,_hash_password, get_user_tweets
from db_tweet_utils import get_tweet, afficher_tweet,post_tweet, _load_tweets, TweetNotFound, TweetTooLong
from db_tweet_utils import _load_tweets
from datetime import datetime
import os
import secrets
from flask import flash

app = Flask(__name__, template_folder="../frontend",static_folder="../static")  # Chemin vers tes templates HTML
app.secret_key = secrets.token_hex(16)
# Route pour afficher le formulaire d'inscription
@app.route('/')
def index():
    return render_template('index.html')



# Route pour traiter l'inscription (méthode POST)
@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    error = None

    # Validation des champs
    if not username or not email or not password:
        error = "Tous les champs sont obligatoires."
    else:
        try:
            # Vérifie si le username ou l'email existe déjà
            test_username(username)
            test_email(email)
            # Ajoute l'utilisateur à la base de données
            add_user(username, email, password)
            return redirect(url_for('success'))  # Redirige vers une page de succès->on veut être redirigé vers la page de login
        except UsernameExistsError as e:
            error = str(e)
        except EmailExistsError as e:
            error = str(e)
        except InvalidPasswordError as e:
            error = str(e)

    # Si erreur, réaffiche le formulaire avec le message d'erreur
    return render_template('index.html', error=error)


# Route pour modifier son profil
@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'username' not in session:
        return redirect(url_for('login'))

    current_user = get_user(session['username'])
    if not current_user:
        return redirect(url_for('login'))

    if request.method == 'GET':
        # Affiche le formulaire d'édition avec les valeurs actuelles
        return render_template('edit_profile.html', user=current_user)

    # === POST ===
    new_email = request.form.get('email') or None
    new_username = request.form.get('username') or None
    new_password = request.form.get('password') or None

    errors = []

    # Vérifications (sans modifier la DB tant que tout n'est pas validé)
    # test_email/test_username/test_password peuvent renvoyer False ou lever des erreurs :
    try:
        if new_email:
            valid = test_email(new_email)
            if not valid:
                errors.append("Adresse e-mail invalide ou déjà utilisée.")
    except Exception as e:
        # Si tes fonctions lèvent des exceptions, on capture et on affiche un message lisible
        errors.append(f"Erreur validation email : {str(e)}")

    try:
        if new_username:
            valid = test_username(new_username)
            if not valid:
                errors.append("Nom d’utilisateur invalide ou déjà pris.")
    except Exception as e:
        errors.append(f"Erreur validation username : {str(e)}")

    try:
        if new_password:
            valid = test_password(new_password)
            if not valid:
                errors.append("Mot de passe trop faible ou non conforme.")
    except Exception as e:
        errors.append(f"Erreur validation mot de passe : {str(e)}")

    # Si erreurs -> rester sur la page d'édition et afficher les erreurs (ne rien sauver)
    if errors:
        return render_template(
            'edit_profile.html',
            errors=errors,
            user=current_user,
            # Pré-remplir les champs côté client si tu veux (attention au password)
            form_email=new_email or current_user.get('email', ''),
            form_username=new_username or current_user.get('username', '')
        )

    # Pas d'erreurs -> mettre à jour en une seule passe
    db = _load_db()
    updated = False
    for u in db.get("users", []):
        if u.get("username") == session['username']:
            if new_email:
                u["email"] = new_email
            if new_username:
                u["username"] = new_username
                session['username'] = new_username  # mettre à jour la session
            if new_password:
                hashed, salt = _hash_password(new_password)
                u["password_hash"] = hashed
                u["salt"] = salt
            updated = True
            break

    if updated:
        _save_db(db)
        # Recharger l'utilisateur mis à jour pour l'affichage
        user_after = get_user(session['username'])
        return render_template(
            'profile.html',
            success="Votre profil a été mis à jour avec succès !",
            user=user_after
        )
    else:
        # Cas improbable : l'utilisateur n'a pas été trouvé dans la DB (race condition)
        errors = ["Impossible de retrouver l'utilisateur dans la base de données."]
        return render_template('edit_profile.html', errors=errors, user=current_user)
    

# Route pour afficher le profil (accessible uniquement si connecté)
@app.route('/profile')
def profile():
    print("Contenu de la session:", session)  # Affiche le contenu de la session
    if 'username' not in session:
        return redirect(url_for('login'))  # Redirige vers la page de login si non connecté
    username = session['username']
    print(f"Username dans session: {username}")
    user = get_user(username)
    tweets = get_user_tweets(username)
    print(f"User récupéré: {user}")  # Affiche l'utilisateur

    if not user:
        print("Aucun utilisateur trouvé !")
        return "Utilisateur non trouvé", 404
    return render_template('profile.html', user=user, tweets=tweets)

#route timeline
@app.route('/timeline')
def timeline():
    if 'username' not in session:
        return redirect(url_for('login'))  # Redirige vers le login si non connecté
    else :
        db = _load_tweets()
        tweets = db.get("tweets", [])
        # Tri décroissant (tweets les plus récents d’abord)
        tweets = sorted(tweets, key=lambda t: t["date"], reverse=True)

        # Reformater la date pour affichage
        for t in tweets:
            try:
                t["date"] = t["date"].replace("T", "  ")[:17]
            except Exception:
                pass  # si jamais une date est déjà formatée, on ignore

        return render_template("timeline.html", tweets=tweets)

@app.route("/post_tweet", methods=["POST"])
def post_tweet_route():
    try:
        content = request.form.get('tweet')  # nom du champ dans ton <textarea>
        username = session['username']

        if not content or content.strip() == "":
            return redirect(url_for('timeline'))  # rien à poster → on revient à la timeline

        post_tweet(username, content)  # ta fonction enregistre le tweet dans la DB des tweets  
        return redirect(url_for('timeline'))  # recharge la timeline avec le nouveau tweet

    except TweetTooLong as e:
        print(e)
        return redirect(url_for('timeline'))
    except Exception as e:
        print("Erreur lors du post :")
        traceback.print_exc()
        return redirect(url_for('timeline'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('index.html')
    email = request.form.get('email')
    password = request.form.get('password')
    error = None
    if not email or not password:
        error = "Email et mot de passe sont obligatoires."
    else:
        user = get_user_by_email(email)
        if user and authenticate(user['username'], password):
            session['username'] = user['username']  # Démarre la session
            return redirect(url_for('timeline'))
        error = "Email ou mot de passe incorrect."
    return render_template('index.html', error=error)


# Route pour la page de succès
@app.route('/success')
def success():
    flash("Compte créé avec succès ! Vous pouvez maintenant vous connecter.")
    return redirect(url_for('login', form_type='login'))

@app.route('/login_success')
def login_success():
    return "Connexion réussie ! Bienvenue sur votre compte."

# Route pour la barre de recherche
@app.route("/explore")
def explore():
    return render_template("explore.html")

# Route pour chercher user
@app.route("/search_user")
def search_user():
    query = request.args.get("q", "").strip().lower()

    db =_load_db()
    users = db["users"]

    # Filtrer les usernames commençant par la requête
    matches = sorted(
        [u["username"] for u in users if u["username"].lower().startswith(query)]
    )

    return jsonify(matches)

# Route pour afficher le profil d'un username
@app.route("/profile/<username>")
def profile_by_name(username):
    user = get_user(username)
    if user:
        return render_template("profile.html", user=user, tweets=get_user_tweets(username))

    # sinon → suggestions
    db = _load_db()
    suggestions = [u["username"] for u in db["users"] if username.lower() in u["username"].lower()]

    return render_template("user_not_found.html", query=username, suggestions=suggestions)




if __name__ == '__main__':
    app.run(debug=True, port=5000)


