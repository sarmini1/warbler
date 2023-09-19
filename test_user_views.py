"""User view tests."""

import os
from unittest import TestCase
from flask import session

from models import db, User, Message, Follows, Like

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"
from app import app

app.config['WTF_CSRF_ENABLED'] = False


# db.drop_all()
db.create_all()


class UserAuthViewTestCase(TestCase):
    """Test user authentication routes."""

    def setUp(self):
        """Add sample data """

        # Need to empty out join table first to respect foreign key constraints
        Like.query.delete()
        Message.query.delete()
        Follows.query.delete()
        User.query.delete()

        self.client = app.test_client()

        test_user = User.signup(
            username="test_user",
            email="test@test.com",
            password="test_userpass",
            image_url=None
        )

        db.session.commit()
        self.test_user_id = test_user.id

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
                    'username': 'test_user',
                    'password': 'test_userpass'
                }
            )
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, "/")

    def test_login_valid_creds_redirect_followed(self):
        """Can a user login with valid credentials and see
        the correct homepage?"""

        with app.test_client() as client:
            resp = client.post(
                "/login",
                data={
                    'username': 'test_user',
                    'password': 'test_userpass'
                },
                follow_redirects=True
            )
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("@test_user", html)

    def test_login_invalid_creds_redirect(self):
        """Can a user login with invalid credentials and see
        the correct page?"""

        with app.test_client() as client:
            resp = client.post(
                "/login",
                data={
                    'username': 'test_user',
                    'password': 'test_userpass1'
                }
            )
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Invalid credentials", html)
            self.assertNotIn("Log out", html)

    def test_signup_form_displays(self):
        """Can a user get to the signup form?"""

        with app.test_client() as client:
            resp = client.get("/signup")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Join Warbler today.", html)

    def test_signup_valid_creds_redirect_followed(self):
        """Can a user sign up with valid credentials and see
        the correct homepage?"""

        with app.test_client() as client:
            resp = client.post(
                "/signup",
                data={
                    'username': 'newuser',
                    'password': 'newuserpass',
                    'email': 'new@new.com'
                },
                follow_redirects=True
            )
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("@newuser", html)

    def test_signup_invalid_creds_redirect_followed(self):
        """Can a user sign up with invalid credentials and get
        redirected back to the signup form?"""

        with app.test_client() as client:
            resp = client.post(
                "/signup",
                data={
                    'username': 'test_user',
                    'password': 'testpass',
                    'email': 'test@test.com'
                },
                follow_redirects=True
            )
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Join Warbler today.", html)
            self.assertIn("Username already taken", html)
            self.assertNotIn("@newuser", html)

    def test_logout_works_for_auth_user(self):
        """Can a logged-in user successfully log out?"""

        with app.test_client() as client:
            with client.session_transaction() as change_session:
                change_session['curr_user'] = self.test_user_id

            resp = client.post("/logout", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertTrue('curr_user' not in session)
            self.assertIn('Welcome back.', html)

    def test_logout_redirects_for_anon_user(self):
        """Is an anon user blocked from logging out?"""

        with app.test_client() as client:

            resp = client.post("/logout", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized.', html)

    def test_see_followers(self):
        """When logged in, can a user see the follower page
        for any user?"""

        with app.test_client() as client:

            u2 = User(
                email="viewfollowerstest_user@test.com",
                username="viewfollowerstest_user",
                password="HASHED_PASSWORD"
            )

            db.session.add(u2)
            db.session.commit()  # this marks the end of the transaction
            u2_id = u2.id

            client.post(
                "/login",
                data={
                    'username': 'test_user',
                    'password': 'test_userpass'
                },
                follow_redirects=True
            )

            followers_resp = client.get(f"/users/{u2_id}/followers")
            html = followers_resp.get_data(as_text=True)

            self.assertEqual(followers_resp.status_code, 200)
            self.assertIn("test page for followers", html)


class UserViewTestCase(TestCase):
    """Test general user routes."""

    def setUp(self):
        """Add sample data """

        # Need to empty out join table first to respect foreign key constraints
        Like.query.delete()
        Message.query.delete()
        Follows.query.delete()
        User.query.delete()

        self.client = app.test_client()

        test_user_1 = User.signup(
            username="test_user1",
            email="test1@test.com",
            password="test_user_1pass",
            image_url=None
        )

        test_user_2 = User.signup(
            username="test_user2",
            email="test2@test.com",
            password="test_user_2pass",
            image_url=None
        )

        db.session.commit()
        self.test_user_1_id = test_user_1.id
        self.test_user_2_id = test_user_2.id

    def tearDown(self):
        """Clean up any fouled transaction."""

        db.session.rollback()

    def test_list_all_users(self):
        """Can a logged-in user see all users?"""

        with app.test_client() as client:
            with client.session_transaction() as change_session:
                change_session['curr_user'] = self.test_user_1_id

            resp = client.get("/users", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("test_user2", html)

    def test_search_users(self):
        """Can a logged-in user search users?"""

        with app.test_client() as client:
            with client.session_transaction() as change_session:
                change_session['curr_user'] = self.test_user_1_id

            resp = client.get(
                "/users",
                query_string={"q": "2"},
                follow_redirects=True
            )
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("test_user2", html)
