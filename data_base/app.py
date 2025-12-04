import traceback
from flask import Flask, send_from_directory, request, render_template, redirect, send_file, url_for, session, jsonify, flash, Response 
import base64
import json
from db_auth_utils import *
from db_tweet_utils import *
from db_tweet_utils import _load_tweets, _save_tweets
from db_auth_utils import _load_db, _save_db, _hash_password
from datetime import datetime
import os
import secrets

app = Flask(__name__, template_folder="../frontend", static_folder="../static")
app.secret_key = secrets.token_hex(16)
UPLOAD_FOLDER = os.path.join(app.root_path, '..', 'static', 'uploads')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov'}  # Extensions autorisées

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# ================================================
# CONTEXT PROCESSOR → session dispo partout !
# ================================================
@app.context_processor
def inject_session():
    return {'session': session}

# Optionnel mais ultra pratique : current_user dispo partout aussi
@app.context_processor
def inject_user():
    if 'username' in session:
        return {'current_user': get_user(session['username'])}
    return {'current_user': None}

# ================================================
# ROUTES
# ================================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    error = None

    if not username or not email or not password:
        error = "Tous les champs sont obligatoires."
    else:
        try:
            test_username(username)
            test_email(email)
            add_user(username, email, password)
            flash("Compte créé avec succès ! Vous pouvez maintenant vous connecter.")
            return redirect(url_for('login'))
        except UsernameExistsError as e:
            error = str(e)
        except EmailExistsError as e:
            error = str(e)
        except InvalidPasswordError as e:
            error = str(e)

    return render_template('index.html', error=error)

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
            session['username'] = user['username']
            return redirect(url_for('timeline'))
        error = "Email ou mot de passe incorrect."

    return render_template('index.html', error=error)

@app.route('/timeline')
def timeline():
    if 'username' not in session:
        return redirect(url_for('login'))

    db = _load_tweets()
    tweets = db.get("tweets", [])
    tweets = sorted(tweets, key=lambda t: t["date"], reverse=True)

    for t in tweets:
        try:
            t["date"] = t["date"].replace("T", " ")[:16]
        except:
            pass

    return render_template(
        "timeline.html",
        tweets=tweets,
        has_user_liked=has_user_liked,       # ← 1) rendre dispo dans Jinja
        get_likes_count=get_likes_count      # ← 2) rendre dispo dans Jinja
    )

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.route("/post_tweet", methods=["POST"])
def post_tweet_route():
    if 'username' not in session:
        return redirect(url_for('login'))

    content = request.form.get('tweet', '').strip()
    media_path=None
    #print(allowed_file(media.filename))
    from werkzeug.utils import secure_filename
    media = request.files.get('media')
    if media and allowed_file(media.filename):
        filename = secure_filename(media.filename)
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        print("DEBUG — app.root_path =", app.root_path)
        print("DEBUG — UPLOAD_FOLDER =", app.config['UPLOAD_FOLDER'])
        print("DEBUG — save_path =", save_path)
        media.save(save_path)
        media_path = f"uploads/{filename}"
    if not content and not media_path:
        flash("Le tweet ne peut pas être vide !")
        return redirect(url_for('timeline'))

    try:
        print("Chemin du média :", media_path)  # Debug
        post_tweet(session['username'], content, media_path)
    except TweetTooLong:
        flash("Ton tweet est trop long ! (max 140 caractères)")
    except Exception as e:
        print("Erreur post tweet :", e)
        traceback.print_exc()

    return redirect(url_for('timeline'))

@app.route('/profile')
def profile():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    user = get_user(username)
    tweets = get_user_tweets(username)

    if not user:
        return "Utilisateur non trouvé", 404

    return render_template('profile.html', user=user, tweets=tweets)

@app.route("/profile/<username>")
def profile_by_name(username):    
    user = get_user(username)
    if user:
        return render_template("profile.html", user=user, tweets=get_user_tweets(username))

    # Suggestions si l'utilisateur n'existe pas
    db = _load_db()
    suggestions = [u["username"] for u in db.get("users", []) if username.lower() in u["username"].lower()]
    return render_template("user_not_found.html", query=username, suggestions=suggestions)



@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'username' not in session:
        return redirect(url_for('login'))

    current_user = get_user(session['username'])
    if not current_user:
        return redirect(url_for('login'))

    if request.method == 'GET':
        return render_template('edit_profile.html', user=current_user)

    new_email = request.form.get('email') or None
    new_username = request.form.get('username') or None
    new_password = request.form.get('password') or None
    errors = []

    # Validation
    if new_email and new_email != current_user['email']:
        try:
            test_email(new_email)
        except Exception as e:
            errors.append(str(e) or "Email invalide ou déjà utilisé.")

    if new_username and new_username != current_user['username']:
        try:
            test_username(new_username)
        except Exception as e:
            errors.append(str(e) or "Pseudo déjà pris.")

    if new_password:
        try:
            test_password(new_password)
        except Exception as e:
            errors.append(str(e) or "Mot de passe trop faible.")

    if errors:
        return render_template('edit_profile.html',
                               user=current_user,
                               errors=errors,
                               form_email=new_email or current_user['email'],
                               form_username=new_username or current_user['username'])

    # Mise à jour en base
    db = _load_db()
    for u in db.get("users", []):
        if u["username"] == session['username']:
            if new_email:
                u["email"] = new_email
            if new_username and new_username != current_user["username"]:
                old_username = current_user["username"]
                u["username"] = new_username

                # Mettre à jour tous les tweets avec l'ancien username
                tweets_db = _load_tweets()
                for tweet in tweets_db.get("tweets", []):
                    if tweet["username"] == old_username:
                        tweet["username"] = new_username
                    if tweet.get("replies"):
                        for r in tweet["replies"]:
                            if r["username"] == old_username:
                                r["username"] = new_username
                _save_tweets(tweets_db)  # n'oublie pas de sauvegarder après modification

                # Mettre à jour la session après avoir changé les tweets
                session['username'] = new_username
            if new_password:
                hashed, salt = _hash_password(new_password)
                u["password_hash"] = hashed
                u["salt"] = salt
            break

    _save_db(db)
    flash("Profil mis à jour avec succès !")
    return redirect(url_for('profile'))

@app.route("/explore")
def explore():
    return render_template("explore.html")

@app.route("/search_user")
def search_user():
    query = request.args.get("q", "").strip().lower()
    db = _load_db()
    users = db.get("users", [])
    matches = sorted([u["username"] for u in users if u["username"].lower().startswith(query)])
    return jsonify(matches)


    


@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    flash('Vous êtes déconnecté.')
    return redirect(url_for('index'))

@app.route("/like/<tweet_id>", methods=["POST"])
def like_route(tweet_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    try:
        like_tweet(tweet_id, session['username'])
    except TweetNotFound:
        pass
    return redirect(request.referrer or url_for('timeline'))

@app.route("/reply/<tweet_id>", methods=["POST"])
def reply_route(tweet_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    content = request.form.get("reply_content", "").strip()
    if content:
        try:
            add_reply(tweet_id, session['username'], content)
        except (TweetNotFound, TweetTooLong):
            pass
    return redirect(request.referrer or url_for('timeline'))

@app.route('/supp_tweet/<tweet_id>', methods=['POST'])
def supp_tweet(tweet_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    try:
        delete_tweet(tweet_id)
    except TweetNotFound:
        pass
    return redirect(url_for('profile'))

@app.route('/delete_account', methods=['POST'])
def delete_account():
    username = session.get('username')
    if username:
        delete_user(username)
        session.clear()
        flash('Votre compte a été définitivement supprimé.')
    else:
        flash('Aucun compte connecté.')
    return redirect(url_for('index'))
# Ajout d'une photo de profil
def load_db():
    with open("database_auth.json", "r") as f:
        return json.load(f)


def save_db(data):
    with open("database_auth.json", "w") as f:
        json.dump(data, f, indent=4)


@app.route('/upload_pfp', methods=['POST'])
def upload_pfp():
    if 'username' not in session:
        return redirect(url_for('login'))

    file = request.files.get('pfp')
    if not file:
        flash("Aucune photo sélectionnée")
        return redirect(request.referrer)
    

    # 1️⃣ Lire l'image
    image_bytes = file.read()

    # 2️⃣ Convertir en base64
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")

    # 3️⃣ Charger DB JSON
    db = load_db()

    # 4️⃣ Trouver l'utilisateur
    for user in db["users"]:
        if user["username"] == session["username"]:
            user["profile_picture"] = image_base64
            break

    # 5️⃣ Sauvegarder
    save_db(db)

    flash("Photo de profil mise à jour !")
    return redirect(url_for('edit_profile'))

#affichage de la pp
@app.route('/pfp/<username>')
def pfp(username):
    db = load_db()

    for user in db["users"]:
        if user["username"] == username:
            if user.get("profile_picture"):
                # Convertir base64 → bytes
                img = base64.b64decode(user["profile_picture"])
                return Response(img, mimetype="image/*")

    # Si pas de photo → image par défaut
    return send_file("../static/images/default_pfp.jpg")

@app.route('/add_bio', methods=['POST'])
def add_bio():
    if 'username' not in session:
        return redirect(url_for('login'))

    new_bio = request.form.get('bio', '').strip()
    db = _load_db()

    for u in db.get("users", []):
        if u["username"] == session['username']:
            
            # Si la clé bio n’existe pas OU n'est pas une string : on la force en string
            if "bio" not in u or not isinstance(u["bio"], str):
                u["bio"] = ""

            # On remplace par la nouvelle valeur
            u["bio"] = new_bio
            break

    _save_db(db)
    flash("Biographie mise à jour avec succès !")
    return redirect(url_for('edit_profile'))

@app.route('/report/<tweet_id>')
def report_tweet(tweet_id):
    if "username" not in session:
        flash("Vous devez être connecté pour signaler un tweet.")
        return redirect(url_for("login"))

    current_user = session["username"]
    db = _load_tweets()
    tweets = db.get("tweets", [])

    reported_tweet = None

    # Chercher le tweet
    for t in tweets:
        if t["tweet_id"] == tweet_id:

            # Initialiser le compteur et la liste des reporters si absents
            if "reports" not in t or not isinstance(t["reports"], int):
                t["reports"] = 0

            if "reporters" not in t or not isinstance(t["reporters"], list):
                t["reporters"] = []

            # Vérifier si l'utilisateur a déjà signalé ce tweet
            if current_user in t["reporters"]:
                flash("Vous avez déjà signalé ce tweet.")
                _save_tweets(db)
                return redirect(request.referrer or url_for('timeline'))

            # Ajouter ce user comme reporter
            t["reporters"].append(current_user)

            # Incrémenter
            t["reports"] += 1
            reported_tweet = t
            break

    # Supprimer si 3 reports ou plus
    if reported_tweet and reported_tweet["reports"] >= 3:
        tweets.remove(reported_tweet)
        flash("Tweet supprimé après 3 signalements.")
    else:
        flash("Tweet signalé.")

    _save_tweets(db)
    return redirect(request.referrer or url_for('timeline'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
