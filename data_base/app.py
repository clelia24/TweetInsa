import traceback
from flask import Flask, request, render_template, redirect, url_for, session
from data_base.db_auth_utils import *
from data_base.db_auth_utils import _load_db,_save_db,_hash_password, get_user_tweets
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

    if request.method == 'POST':
        new_email = request.form.get('email')
        new_password = request.form.get('password')

        # Mettre à jour l'email et le mot de passe
        db = _load_db()
        for u in db["users"]:
            if u["username"] == session['username']:
                if new_email:
                    u["email"] = new_email
                if new_password:
                    hashed, salt = _hash_password(new_password)
                    u["password_hash"] = hashed
                    u["salt"] = salt
                _save_db(db)
                break

        return redirect(url_for('profile'))

    return render_template('edit_profile.html')

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

if __name__ == '__main__':
    app.run(debug=True, port=5000)


