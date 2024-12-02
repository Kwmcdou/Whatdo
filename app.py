import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required

# Configure application
app = Flask(__name__)

# Enable debug mode
app.config['DEBUG'] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///whatdo.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route("/create_event", methods=["GET", "POST"])
@login_required
def create_event():
    """Create a new event"""
    if request.method == "POST":
        event_name = request.form.get("event_name")

        # Ensure the event name was provided
        if not event_name:
            return apology("must provide event name", 400)

        prompt_g = "What would you like to accomplish this week?"
        # Store event name with default prompt
        db.execute("INSERT INTO events (name, prompt_g) VALUES (?, ?)", event_name, prompt_g)

        event_id = db.execute("SELECT id FROM events WHERE name = ?", event_name)[0]["id"]

        # Update user_events
        db.execute("INSERT INTO user_events (user_id, event_id) VALUES (?, ?)", session["user_id"], event_id)

        return render_template("event.html", prompt_g=prompt_g, event_name=event_name, event_id=event_id)

    return render_template("createEvent.html")

@app.route("/event/<int:event_id>")
@login_required
def event(event_id):
    """Display an event and its cards"""
    # Fetch the event details
    event = db.execute("SELECT * FROM events WHERE id = ?", event_id)
    if not event:
        return apology("Event not found", 404)

    # Fetch the cards for this event
    cards = db.execute("SELECT * FROM cards WHERE event_id = ?", event_id)

    # Render the event page with its cards
    return render_template("event.html", event_id=event_id, cards=cards, prompt_g=event[0]["prompt_g"])

@app.route("/create_card", methods=["GET", "POST"])
@login_required
def create_card():
    """Create a new card for an event"""
    if request.method == "POST":
        content = request.form.get("content")
        event_id = request.form.get("event_id")

        # Ensure content was provided
        if not content:
            return apology("must provide content", 400)

        # Insert the new card into the database
        db.execute("INSERT INTO cards (event_id, user_id, content) VALUES (?, ?, ?)",
                   event_id, session["user_id"], content)

        # Redirect to the event page to prevent resubmission
        return redirect(f"/event/{event_id}")

    return render_template("event.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")



@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Ensure confirmation was submitted
        elif not request.form.get("confirmation"):
            return apology("must confirm password", 400)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username is not duplicate and password is correct
        if len(rows) == 1:
            return apology("username is already taken", 400)

        if request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords do not match", 400)

        # insert valid username and password to db
        hash = generate_password_hash(request.form.get("password"))
        db.execute(
            "INSERT INTO users (username, hash) VALUES (? , ?)", request.form.get("username"), hash
        )

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")

