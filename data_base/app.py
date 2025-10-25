from flask import Flask, request, render_template, redirect, url_for
from db_auth_utils import add_user, test_username, test_email, UsernameExistsError, EmailExistsError
from db_tweet_utils import get_tweet, afficher_tweet,post_tweet, _load_tweets, TweetNotFound, TweetTooLong 
from db_tweet_utils import _load_tweets
from datetime import datetime
import os

app = Flask(__name__, template_folder="../frontend", static_folder="../static")  # Chemin vers tes templates HTML

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
            return redirect(url_for('success'))  # Redirige vers une page de succès
        except UsernameExistsError as e:
            error = str(e)
        except EmailExistsError as e:
            error = str(e)

    # Si erreur, réaffiche le formulaire avec le message d'erreur
    return render_template('index.html', error=error)

# Route pour la page de succès
@app.route('/success')
def success():
    return "Compte créé avec succès ! Vous pouvez maintenant vous connecter."


    #------timeline --------
#route pour afficher un tweet 
@app.route('/timeline')
def timeline():
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
        username = "nom personne connectée"  # temporaire : en attendant d'avoir une vraie session utilisateur

        if not content or content.strip() == "":
            return redirect(url_for('timeline'))  # rien à poster → on revient à la timeline

        post_tweet(username, content)  # ta fonction enregistre le tweet dans la DB
        return redirect(url_for('timeline'))  # recharge la timeline avec le nouveau tweet

    except TweetTooLong as e:
        print(e)
        return redirect(url_for('timeline'))
    except Exception as e:
        print("Erreur lors du post :", e)
        return redirect(url_for('timeline'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)

