from flask import Flask, request, render_template, redirect, url_for
from db_auth_utils import add_user, test_username, test_email, UsernameExistsError, EmailExistsError, InvalidPasswordError, authenticate, get_user_by_email
import os

app = Flask(__name__, template_folder="../frontend")  # Chemin vers tes templates HTML

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
        except InvalidPasswordError as e:
            error = str(e)

    # Si erreur, réaffiche le formulaire avec le message d'erreur
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
            return redirect(url_for('login_success'))
        error = "Email ou mot de passe incorrect."
    return render_template('index.html', error=error)


# Route pour la page de succès
@app.route('/success')
def success():
    return "Compte créé avec succès ! Vous pouvez maintenant vous connecter."

@app.route('/login_success')
def login_success():
    return "Connexion réussie ! Bienvenue sur votre compte."

if __name__ == '__main__':
    app.run(debug=True, port=5000)

