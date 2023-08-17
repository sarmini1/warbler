"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_message_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows, Like

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class MessageModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        Follows.query.delete()
        Like.query.delete()
        Message.query.delete()
        User.query.delete()

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        self.client = app.test_client()
        self.user = u

    def test_message_model(self):
        """Does basic model work?"""

        msg = Message(
            text="test message 123",
            user_id=self.user.id
        )

        u2 = User(
            email="test2@test2.com",
            username="testuser2",
            password="HASHED_PASSWORD"
        )

        db.session.add_all([u2, msg])
        db.session.commit()

        # User should have 1 message & no followers
        self.assertEqual(len(self.user.messages), 1)
        self.assertEqual(len(self.user.followers), 0)

        # Should be able to review full user object from msg
        self.assertEqual(self.user, msg.user)

        # User 2 should have no messages and no followers
        self.assertEqual(len(u2.messages), 0)
        self.assertEqual(len(u2.followers), 0)

    def test_msg_repr(self):
        """Does the message repr method return what we expect?"""

        msg = Message(
            text="test message 123",
            user_id=self.user.id
        )

        db.session.add(msg)
        db.session.commit()

        self.assertEqual(
            f'{msg}',
            f"<Message #{msg.id}, Author ID:{msg.user_id}>"
        )

    def test_like_msg(self):
        """Can a user like another user's message?"""

        u2 = User(
            email="testlike2@testlike2.com",
            username="testlikeuser2",
            password="HASHED_PASSWORD"
        )

        db.session.add(u2)
        db.session.commit()

        msg = Message(
            text="test like message 123",
            user_id=u2.id
        )

        db.session.add(msg)
        db.session.commit()

        like = Like(
            user_id=self.user.id,
            message_id=msg.id
        )

        db.session.add(like)
        db.session.commit()

        self.assertEqual(len(self.user.liked_messages), 1)

    def test_unlike_msg(self):
        """Can a user unlike another user's message?"""

        u2 = User(
            email="testlike2@testlike2.com",
            username="testlikeuser2",
            password="HASHED_PASSWORD"
        )

        db.session.add(u2)
        db.session.commit()

        msg = Message(
            text="test like message 123",
            user_id=u2.id
        )

        db.session.add(msg)
        db.session.commit()

        like = Like(
            user_id=self.user.id,
            message_id=msg.id
        )

        db.session.add(like)
        db.session.commit()
        self.user.liked_messages.remove(msg)
        db.session.commit()

        self.assertEqual(len(self.user.liked_messages), 0)

    # def test_cannot_like_self_msgs(self):
    #     """Is a user unable to like their own messages?"""

    #     msg = Message(
    #         text="test like message 123",
    #         user_id=self.user.id
    #     )

    #     db.session.add(msg)
    #     db.session.commit()

    #     like = Like(
    #         user_id=self.user.id,
    #         message_id=msg.id
    #     )
    #     db.session.add(like)
    #     db.session.commit()

  #TODO change like functionality to be a helper function that we can
  # call in our tests (unless this test should be handled in route tests)
