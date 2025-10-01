import unittest
import tempfile
import os
import db_auth_utils as auth


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
        auth.add_user("alice", "alice@example.com", "pass123")
        self.assertEqual(auth.count_users(), 1)
        user = auth.get_user("alice")
        self.assertIsNotNone(user)
        self.assertEqual(user["email"], "alice@example.com")

    def test_add_user_existing_username(self):
        auth.add_user("bob", "bob@example.com", "pass123")
        with self.assertRaises(auth.UsernameExistsError):
            auth.add_user("bob", "bob2@example.com", "pass456")

    def test_add_user_existing_email(self):
        auth.add_user("carol", "carol@example.com", "pass123")
        with self.assertRaises(auth.EmailExistsError):
            auth.add_user("carol2", "carol@example.com", "pass456")

    def test_get_user_by_email(self):
        auth.add_user("dave", "dave@example.com", "pass123")
        user = auth.get_user_by_email("dave@example.com")
        self.assertEqual(user["username"], "dave")
        self.assertIsNone(auth.get_user_by_email("unknown@example.com"))

    def test_authenticate(self):
        auth.add_user("eve", "eve@example.com", "mypassword")
        self.assertTrue(auth.authenticate("eve", "mypassword"))
        self.assertFalse(auth.authenticate("eve", "wrongpass"))
        self.assertFalse(auth.authenticate("unknown", "mypassword"))

    def test_delete_user(self):
        auth.add_user("frank", "frank@example.com", "pass123")
        auth.delete_user("frank")
        self.assertIsNone(auth.get_user("frank"))
        self.assertEqual(auth.count_users(), 0)
        with self.assertRaises(auth.UserNotFoundError):
            auth.delete_user("frank")


if __name__ == "__main__":
    unittest.main()
