import unittest
import tempfile
import os
import db_tweet_utils as tweets
import data_base.db_auth_utils as auth_utils

class TestDBTweetsUtils(unittest.TestCase):

    def setUp(self):
        # DB tweets temporaire
        self.tmp_db = tempfile.NamedTemporaryFile(delete=False)
        self.tmp_db.close()
        tweets.DB_FILE = self.tmp_db.name

        # DB auth temporaire
        self.tmp_auth_db = tempfile.NamedTemporaryFile(delete=False)
        self.tmp_auth_db.close()
        auth_utils.DB_FILE = self.tmp_auth_db.name

        # DB auth vide
        with open(auth_utils.DB_FILE, "w", encoding="utf-8") as f:
            f.write('{"users": []}')

    def tearDown(self):
        if os.path.exists(self.tmp_db.name):
            os.remove(self.tmp_db.name)
        if os.path.exists(self.tmp_auth_db.name):
            os.remove(self.tmp_auth_db.name)

    def _create_user(self, username):
        # Crée un user dans la DB auth temporaire
        db = {"users": [{"username": username, "tweets_posted": []}]}
        with open(auth_utils.DB_FILE, "w", encoding="utf-8") as f:
            import json
            json.dump(db, f)

    def test_post_and_get_tweet(self):
        self._create_user("alice")
        tweet = tweets.post_tweet("alice", "Hello World!")
        self.assertIn("tweet_id", tweet)
        t_id = tweet["tweet_id"]
        fetched = tweets.get_tweet(t_id)
        self.assertEqual(fetched["username"], "alice")
        self.assertEqual(fetched["content"], "Hello World!")

    def test_tweet_too_long(self):
        self._create_user("bob")
        long_text = "x" * 141
        with self.assertRaises(tweets.TweetTooLong):
            tweets.post_tweet("bob", long_text)

    def test_delete_tweet(self):
        self._create_user("bob")
        tweet = tweets.post_tweet("bob", "To delete")
        t_id = tweet["tweet_id"]
        tweets.delete_tweet(t_id)
        with self.assertRaises(tweets.TweetNotFound):
            tweets.get_tweet(t_id)

    def test_select_random_tweet(self):
        self._create_user("carol")
        ids = [tweets.post_tweet("carol", f"Tweet {i}")["tweet_id"] for i in range(5)]
        rand_id = tweets.select_random_tweet()
        self.assertIn(rand_id, ids)

    def test_get_tweet_not_found(self):
        with self.assertRaises(tweets.TweetNotFound):
            tweets.get_tweet("nonexistent")

    def test_delete_tweet_not_found(self):
        with self.assertRaises(tweets.TweetNotFound):
            tweets.delete_tweet("nonexistent")

if __name__ == "__main__":
    unittest.main()
