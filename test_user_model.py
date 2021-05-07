"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        Follows.query.delete()
        User.query.delete()
        Message.query.delete()

        # TODO add some sample data into here
        # and utilize 'self' to call in below tests

        self.client = app.test_client()

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

    def test_user_repr_method(self):
        """Does the repr method display the correct info?"""

        u = User(
            email="reprtest@test.com",
            username="reprtestuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()
        user = User.query.filter(User.username == "reprtestuser").first()
        # breakpoint()
        self.assertEqual(
                        f'{user}',
                        f"<User #{user.id}: {user.username}, {user.email}>")

    def test_following_another_user(self):
        """Does is_following method successfully detect when user1 follows user2?"""

        u1 = User(
            email="followingtestuser1@test.com",
            username="followingtestuser1",
            password="HASHED_PASSWORD"
        )

        u2 = User(
            email="followingtestuser2@test.com",
            username="followingtestuser2",
            password="HASHED_PASSWORD"
        )

        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()

        test_follow = Follows(
                            user_being_followed_id=u2.id,
                            user_following_id=u1.id)
        db.session.add(test_follow)
        db.session.commit()
        test_is_following = u1.is_following(u2)
        test_followed_by = u2.is_followed_by(u1)
        self.assertEqual(test_is_following, True)
        self.assertEqual(test_followed_by, True)

    def test_not_following_another_user(self):
        """Does is_following method successfully detect when user1
        isn't following user2?"""

        u1 = User(
            email="followingtestuser1@test.com",
            username="followingtestuser1",
            password="HASHED_PASSWORD"
        )

        u2 = User(
            email="followingtestuser2@test.com",
            username="followingtestuser2",
            password="HASHED_PASSWORD"
        )

        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()

        test_is_following = u1.is_following(u2)
        test_is_followed_by = u2.is_followed_by(u1)
        self.assertEqual(test_is_following, False)
        self.assertEqual(test_is_followed_by, False)

    def test_signup_valid(self):
        """Does signup class method successfully create a new user
            when given valid credentials?"""

        credentials = {
                            "username": "signup_user",
                            "email": "signup@user.com",
                            "password": "something",
                            "image_url": "/static/images/default-pic.png"}

        User.signup(**credentials)
        db.session.commit()
        # breakpoint()
        signup_user_record = User.query.filter(User.username == "signup_user").first()
        self.assertIsNotNone(signup_user_record)

    def test_signup_invalid(self):
        """Does signup class method successfully create a new user
            when given invalid credentials?"""

        credentials = {
                            "username": 23980,
                            "email": "signup@user.com",
                            "password": "something",
                            "image_url": "/static/images/default-pic.png"}

        User.signup(**credentials)
        db.session.commit()
        # breakpoint()
        signup_user_record = User.query.filter(User.username == "signup_user").first()
        self.assertIsNone(signup_user_record)

    def test_authenticate_valid_user(self):
        """Does the authenticate method successfully return a user
        when given valid credentials?"""

        credentials = {
                            "username": "authed_user",
                            "email": "auth@user.com",
                            "password": "something",
                            "image_url": "/static/images/default-pic.png"}

        User.signup(**credentials)
        db.session.commit()
        user = User.authenticate("authed_user", "something")
        # breakpoint()
        self.assertEqual(
                        f'{user}',
                        f"<User #{user.id}: {user.username}, {user.email}>")

    def test_authenticate_invalid_username(self):
        """Does the authenticate method successfully return a user
        when given an invalid username?"""

        credentials = {
                            "username": "authed_user",
                            "email": "auth@user.com",
                            "password": "something",
                            "image_url": "/static/images/default-pic.png"}

        User.signup(**credentials)
        db.session.commit()
        user = User.authenticate("not_authed_user", "something")
        # breakpoint()
        self.assertEqual(user, False)

    def test_authenticate_invalid_pw(self):
        """Does the authenticate method successfully return a user
        when given an invalid password?"""

        credentials = {
                            "username": "authed_user",
                            "email": "auth@user.com",
                            "password": "something",
                            "image_url": "/static/images/default-pic.png"}

        User.signup(**credentials)
        db.session.commit()
        user = User.authenticate("authed_user", "something_else")
        # breakpoint()
        self.assertEqual(user, False)
