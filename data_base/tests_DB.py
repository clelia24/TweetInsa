import unittest
import tempfile
import os
from . import db_auth_utils as auth


#### Tests faits sur une DB temporaire ####


class TestDBAuthUtils(unittest.TestCase):

    def setUp(self):
        """
        Crée un fichier temporaire pour la DB et redirige le module vers ce fichier.
        """
        self.tmp_db = tempfile.NamedTemporaryFile(delete=False)
        self.tmp_db.close()  # on a juste besoin du chemin
        auth.DB_FILE = self.tmp_db.name
        auth._refresh_count()  # initialise NB_USERS à 0

    def tearDown(self):
        """
        Supprime le fichier temporaire après chaque test.
        """
        if os.path.exists(self.tmp_db.name):
            os.remove(self.tmp_db.name)

    def test_add_user_and_count(self):
        auth.add_user("alice", "alice@example.com", "Paass123")
        self.assertEqual(auth.count_users(), 1)
        user = auth.get_user("alice")
        self.assertIsNotNone(user)
        self.assertEqual(user["email"], "alice@example.com")

    def test_add_user_existing_username(self):
        auth.add_user("bob", "bob@example.com", "Paass123")
        with self.assertRaises(auth.UsernameExistsError):
            auth.add_user("bob", "bob2@example.com", "pass456")

    def test_add_user_existing_email(self):
        auth.add_user("carol", "carol@example.com", "Paass123")
        with self.assertRaises(auth.EmailExistsError):
            auth.add_user("carol2", "carol@example.com", "Paass456")

    def test_get_user_by_email(self):
        auth.add_user("dave", "dave@example.com", "Paass123")
        user = auth.get_user_by_email("dave@example.com")
        self.assertEqual(user["username"], "dave")
        self.assertIsNone(auth.get_user_by_email("unknown@example.com"))

    def test_authenticate(self):
        auth.add_user("eve", "eve@example.com", "Mypassword8")
        self.assertTrue(auth.authenticate("eve", "Mypassword8"))
        self.assertFalse(auth.authenticate("eve", "wrongpass"))
        self.assertFalse(auth.authenticate("unknown", "mypassword"))

    def test_delete_user(self):
        auth.add_user("frank", "frank@example.com", "Paass123")
        auth.delete_user("frank")
        self.assertIsNone(auth.get_user("frank"))
        self.assertEqual(auth.count_users(), 0)
        with self.assertRaises(auth.UserNotFoundError):
            auth.delete_user("frank")

    def test_follow_unfollow(self):
        # Créer deux utilisateurs
        auth.add_user("alice", "alice@example.com", "Paass123")
        auth.add_user("bob", "bob@example.com", "Paass456")

        # Alice suit Bob
        auth.follow("alice", "bob")

        user_alice = auth.get_user("alice")
        user_bob = auth.get_user("bob")

        # Vérifier que les relations sont correctes
        self.assertIn("bob", user_alice.get("followed", []))
        self.assertIn("alice", user_bob.get("followers", []))

        # Alice arrête de suivre Bob
        auth.unfollow("alice", "bob")

        user_alice = auth.get_user("alice")
        user_bob = auth.get_user("bob")

        # Vérifier que les relations ont été supprimées
        self.assertNotIn("bob", user_alice.get("followed", []))
        self.assertNotIn("alice", user_bob.get("followers", []))


    def test_follow_errors(self):
        # Créer un utilisateur
        auth.add_user("alice", "alice@example.com", "Paass123")

        # Essayer de suivre un utilisateur qui n'existe pas
        with self.assertRaises(auth.UserNotFoundError):
            auth.follow("alice", "bob")

        # Essayer d'un utilisateur inexistant
        with self.assertRaises(auth.UserNotFoundError):
            auth.follow("bob", "alice")

    def test_unfollow_errors(self):
        # Créer deux utilisateurs
        auth.add_user("alice", "alice@example.com", "Paass123")
        auth.add_user("bob", "bob@example.com", "Paass456")

        # Essayer d'unfollow sans avoir suivi
        with self.assertRaises(auth.UserNotFoundError):
            auth.unfollow("alice", "bob")

        # Alice suit Bob correctement
        auth.follow("alice", "bob")

        # Supprimer Alice de la DB et tenter unfollow
        auth.delete_user("alice")
        with self.assertRaises(auth.UserNotFoundError):
            auth.unfollow("alice", "bob")

if __name__ == "__main__":
    unittest.main()
