import os

from flask import Flask, render_template, request, flash, redirect, session, g
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError

from forms import (
    UserAddForm,
    LoginForm,
    MessageForm,
    EditProfileForm,
    CSRFValidationForm
)
from models import db, connect_db, User, Message, Like

# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.
database_url = os.environ.get('DATABASE_URL', 'postgresql:///warbler')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")
toolbar = DebugToolbarExtension(app)

connect_db(app)

CURR_USER_KEY = "curr_user"

##############################################################################
# User signup/login/logout


@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""
    # this happens before every request since it's the view
    # function for the before_request decorator

    # TODO look into flask middleware for this

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]
        return True


@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If there already is a user with that username: flash message
    and re-present form.
    """

    form = UserAddForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
                image_url=form.image_url.data or User.image_url.default.arg,
            )
            db.session.commit()

        except IntegrityError:
            flash("Username already taken", 'danger')
            db.session.rollback()
            return render_template('users/signup.html', form=form)

        do_login(user)

        return redirect("/")

    else:
        return render_template('users/signup.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data,
                                 form.password.data)

        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")

        flash("Invalid credentials.", 'danger')

    return render_template('users/login.html', form=form)


@app.route('/logout', methods=["GET", "POST"])
def logout():
    """Handle logout of user."""

    form = CSRFValidationForm()

    if form.validate_on_submit():
        if do_logout():
            flash("Successfully logged out!")
            return redirect('/login')
        else:
            flash("You need to be logged in to logout!")
            return redirect('/login')
    else:
        flash("Access unauthorized.", "danger")
        return redirect("/")

# #############################################################################
# General user routes:


@app.route('/users')
def list_users():
    """Page with listing of users.

    Can take a 'q' param in querystring to search by that username.
    """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    search = request.args.get('q')
    form = CSRFValidationForm()

    if not search:
        users = User.query.all()
    else:
        users = User.query.filter(User.username.like(f"%{search}%")).all()

    return render_template('users/index.html', users=users, form=form)


@app.route('/users/<int:user_id>')
def users_show(user_id):
    """Show user profile."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = CSRFValidationForm()
    user = User.query.get_or_404(user_id)

    return render_template('users/show.html', user=user, form=form)


@app.route('/users/<int:user_id>/following')
def show_following(user_id):
    """Show list of people this user is following."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = CSRFValidationForm()
    user = User.query.get_or_404(user_id)
    return render_template('users/following.html', user=user, form=form)


@app.route('/users/<int:user_id>/followers')
def users_followers(user_id):
    """Show list of followers of this user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = CSRFValidationForm()
    user = User.query.get_or_404(user_id)
    return render_template('users/followers.html', user=user, form=form)


@app.route('/users/follow/<int:follow_id>', methods=["GET", "POST"])
def add_follow(follow_id):
    """Add a follow for the currently-logged-in user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = CSRFValidationForm()
    if form.validate_on_submit():
        followed_user = User.query.get_or_404(follow_id)
        g.user.following.append(followed_user)
        db.session.commit()
        # return redirect(f"/users/{g.user.id}/following")
        return redirect(request.referrer)
    else:
        flash("Access unauthorized.", "danger")
        return redirect("/")


@app.route('/users/stop-following/<int:follow_id>', methods=["GET", "POST"])
def stop_following(follow_id):
    """Have currently-logged-in-user stop following this user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = CSRFValidationForm()
    if form.validate_on_submit():
        followed_user = User.query.get(follow_id)
        g.user.following.remove(followed_user)
        db.session.commit()
        # return redirect(f"/users/{g.user.id}/following")
        return redirect(request.referrer)
    else:
        flash("Access unauthorized.", "danger")
        return redirect("/")


@app.route('/users/profile', methods=["GET", "POST"])
def profile():
    """Update profile for current user."""

    # check for failure first
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect('/')

    form = EditProfileForm(obj=g.user)

    # post request route
    if form.validate_on_submit():
        password = form.password.data
        auth_user = User.authenticate(g.user.username, password)
        # if user is authenticated, then check edit profile form inputs
        if auth_user:
            auth_user.username = form.username.data
            auth_user.email = form.email.data
            auth_user.image_url = form.image_url.data
            auth_user.header_image_url = form.header_image_url.data
            auth_user.bio = form.bio.data
            db.session.commit()
            return redirect(f"/users/{g.user.id}")
        else:
            flash("Unauthorized.", "danger")
            return redirect("/")
    # get request route
    else:
        return render_template("users/edit.html", form=form, user=g.user)


@app.route('/users/delete', methods=["GET", "POST"])
def delete_user():
    """Delete user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = CSRFValidationForm()

    if form.validate_on_submit():
        do_logout()
        flash("Successfully deleted!")
        db.session.delete(g.user)
        db.session.commit()
        return redirect("/signup")
    else:
        flash("Access unauthorized.", "danger")
        return redirect("/")


##############################################################################
# Messages routes:

@app.route('/messages/new', methods=["GET", "POST"])
def messages_add():
    """Add a message:

    Show form if GET. If valid, update message and redirect to user page.
    """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = MessageForm()

    if form.validate_on_submit():
        msg = Message(text=form.text.data)
        g.user.messages.append(msg)
        db.session.commit()
        return redirect(f"/users/{g.user.id}")

    return render_template('messages/new.html', form=form)


@app.route('/messages/<int:message_id>', methods=["GET"])
def messages_show(message_id):
    """Show a message."""

    # checking that the current user is logged in may not
    # be super crucial in this route but it can't hurt.
    # TODO may want to change this in some way once the concept of
    # public/private profiles gets introduced

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = CSRFValidationForm()
    msg = Message.query.get(message_id)
    return render_template('messages/show.html', message=msg, form=form)


@app.route('/messages/<int:message_id>/delete', methods=["GET", "POST"])
def messages_destroy(message_id):
    """Delete a message."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = CSRFValidationForm()

    if form.validate_on_submit():
        # before deleting msg from messages table, need to remove from likes
        if Like.query.filter(Like.message_id == message_id).all():
            Like.query.filter(Like.message_id == message_id).all().delete()
            db.session.commit()

        msg = Message.query.get(message_id)
        db.session.delete(msg)
        db.session.commit()
        return redirect(f"/users/{g.user.id}")
    else:
        flash("Access unauthorized.", "danger")
        return redirect("/")


@app.route('/messages/<int:message_id>/like', methods=["GET", "POST"])
def like_message(message_id):
    """Adds a message to logged in user's likes"""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = CSRFValidationForm()

    if form.validate_on_submit():
        msg = Message.query.get_or_404(message_id)
        # TODO refactor referrer line below to find a more reliable method of
        # grabbing the origin of the request given that this setting
        # may be disabled for some users
        origin_of_req = request.referrer

        # TODO additional note here to incorporate like functionality
        # as a method in a class instead

        # only allow users to like OTHER users' posts
        # check for failure first
        if msg.user_id == g.user.id:
            flash("You can't like your own posts!", "danger")
            return redirect(origin_of_req)
        else:
            # append msg to that user's liked messages
            g.user.liked_messages.append(msg)
            db.session.commit()
            return redirect(origin_of_req)
    else:
        flash("Access unauthorized.", "danger")
        return redirect("/")


# think about different HTTP verbs in other contexts
@app.route('/messages/<int:message_id>/unlike', methods=["GET", "POST"])
def unlike_message(message_id):
    """Removes a message from logged in user's likes"""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = CSRFValidationForm()

    if form.validate_on_submit():
        # grab the liked message we want to unlike
        msg = Message.query.get_or_404(message_id)

        # TODO refactor referrer line below to find a more reliable method of
        # grabbing the origin of the request given that this setting
        # may be disabled for some users
        origin_of_req = request.referrer

        # remove from user's list of liked messages
        # TODO additional note here to incorporate unlike functionality
        # as a method in a class instead
        g.user.liked_messages.remove(msg)
        db.session.commit()
        return redirect(origin_of_req)
    else:
        flash("Access unauthorized.", "danger")
        return redirect("/")


@app.route('/users/<int:user_id>/likes')
def show_likes(user_id):
    """Shows liked messages for a particular user"""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    form = CSRFValidationForm()

    # TODO arrange liked messages in desc order by when like occurred
    return render_template("likes.html", user=user, form=form)


##############################################################################
# Homepage and error pages

@app.route('/')
def homepage():
    """Show homepage:

    - anon users: no messages
    - logged in: 100 most recent messages of followed_users
    """
    if g.user:
        # grab the ids of the users that current user is following (& the user)
        users_to_display = [user.id for user in g.user.following] + [g.user.id]
        # only pull in messages from users whose ids are in the above list
        messages = (
            Message
            .query
            .filter(Message.user_id.in_(users_to_display))
            .order_by(Message.timestamp.desc())
            .limit(100)
            .all()
        )
        form = CSRFValidationForm()

        return render_template('home.html', messages=messages, form=form)

    else:
        return render_template('home-anon.html')


##############################################################################
# Turn off all caching in Flask
#   (useful for dev; in production, this kind of stuff is typically
#   handled elsewhere)
#
# https://stackoverflow.com/questions/34066804/disabling-caching-in-flask

@app.after_request
def add_header(response):
    """Add non-caching headers on every request."""

    # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cache-Control
    response.cache_control.no_store = True
    return response
