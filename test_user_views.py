"""User view tests."""

import os
from unittest import TestCase

from models import db, User, Message, Follows, Like
from forms import (
                    MessageForm,
                    UserAddForm,
                    LoginForm,
                    EditProfileForm,
                    CSRFValidationForm)

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"
from app import app

app.config['WTF_CSRF_ENABLED'] = False


# db.drop_all()
db.create_all()


class UserViewTestCase(TestCase):
    """test user routes for warbler app"""

    def setUp(self):
        """Add sample data """

        # Need to empty out join table first to respect foreign key constraints
        Like.query.delete()
        Message.query.delete()
        Follows.query.delete()
        User.query.delete()

        self.client = app.test_client()

        testuser = User.signup(
                                username="testuser",
                                email="test@test.com",
                                password="testuserpass",
                                image_url=None)

        db.session.commit()
        self.testuser_id = testuser.id

    def tearDown(self):
        """Clean up any fouled transaction."""

        db.session.rollback()

    def test_login_valid_creds_redirect(self):
        """Can a user login with valid credentials and see
        the correct homepage?"""

        with app.test_client() as client:
            resp = client.post(
                                "/login",
                                data={
                                    'username': 'testuser',
                                    'password': 'testuserpass'
                                })
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, "/")

    def test_login_valid_creds_redirect_followed(self):
        """Can a user login with valid credentials and see
        the correct homepage?"""

        with app.test_client() as client:
            resp = client.post(
                                "/login",
                                data={
                                    'username': 'testuser',
                                    'password': 'testuserpass'},
                                follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("testuser", html)

    def test_login_invalid_creds_redirect(self):
        """Can a user login with invalid credentials and see
        the correct page?"""

        with app.test_client() as client:
            resp = client.post(
                                "/login",
                                data={
                                    'username': 'testuser',
                                    'password': 'testuserpass1'
                                })
            html = resp.get_data(as_text=True)

            # breakpoint()
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Invalid credentials", html)
            self.assertNotIn("Log out", html)

    def test_see_followers(self):
        """When logged in, can a user see the follower page
        for any user?"""

        with app.test_client() as client:

            u2 = User(
                email="viewfollowerstestuser@test.com",
                username="viewfollowerstestuser",
                password="HASHED_PASSWORD"
            )

            db.session.add(u2)
            db.session.commit()  # this marks the end of the transaction
            u2_id = u2.id

            login_resp = client.post(
                                "/login",
                                data={
                                    'username': 'testuser',
                                    'password': 'testuserpass'},
                                follow_redirects=True)

            followers_resp = client.get(f"/users/{u2_id}/followers")
            html = followers_resp.get_data(as_text=True)

            self.assertEqual(followers_resp.status_code, 200)
            self.assertIn("test page for followers", html)
