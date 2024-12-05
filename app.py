from cs50 import SQL
from datetime import datetime
from flask import Flask, jsonify, redirect, render_template, request, session
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

def fetch_and_verify_event_and_user(event_id, template_name):
    """Fetch event details and verify user permission, then render template."""
    # Fetch event details
    event = db.execute("SELECT * FROM events WHERE id = ?", event_id)
    if not event:
        return apology("Event not found", 404)

    # Verify user permission to the event
    user_event = db.execute("SELECT event_id FROM user_events WHERE user_id = ? AND event_id = ?", session["user_id"],
                            event_id)
    if not user_event:
        return apology("Access denied. You do not have permission for this event", 403)

    # Fetch card details
    cards = db.execute("SELECT * FROM cards WHERE event_id = ? ORDER BY priority_y", event_id)

    return render_template(template_name, event_id=event_id, cards=cards, prompt_g=event[0]["prompt_g"], event_name=event[0]["name"])


@app.template_filter('format_date')
def format_date(value):
    """Formats a datetime object as 'YYYY-MM-DD'"""
    date_obj = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
    return date_obj.strftime('%Y-%m-%d')

@app.route("/")
@login_required
def index():
    """Show home page"""
    # Pull the name of user's events
    events = db.execute("SELECT name, id, timestamp FROM events WHERE id IN (SELECT event_id FROM user_events WHERE user_id = ?)", session["user_id"])

    return render_template("index.html", events=events)

@app.route("/create_event", methods=["GET", "POST"])
@login_required
def create_event():
    """Create a new event"""
    if request.method == "POST":
        event_name = request.form.get("event_name")

        # Ensure the event name was provided
        if not event_name:
            return apology("must provide event name", 400)

        # Default prompt_g
        prompt_g = "What would you like to accomplish?"

        # Store event name with default prompt
        db.execute("INSERT INTO events (name, prompt_g) VALUES (?, ?)", event_name, prompt_g)

        event_id = db.execute("SELECT id FROM events WHERE name = ? ORDER BY id DESC LIMIT 1", event_name)[0]['id']

        # Update user_events
        db.execute("INSERT INTO user_events (user_id, event_id) VALUES (?, ?)", session["user_id"], event_id)

        return redirect(f"/event/{event_id}")

    return render_template("createEvent.html")

@app.route("/view_event/<int:event_id>")
@login_required
def view_event(event_id):
    """Display an event and its cards using 'viewEvent.html'."""
    return fetch_and_verify_event_and_user(event_id, "viewEvent.html")

@app.route("/event/<int:event_id>")
@login_required
def event(event_id):
    """Display an event and its cards using 'event.html'."""
    return fetch_and_verify_event_and_user(event_id, "event.html")

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

@app.route('/start_comparison', methods=['POST'])
@login_required
def start_comparison():
    """Fetch the first two items for comparison in an event."""
    data = request.get_json()
    event_id = data.get('event_id')

    # Reset priority for cards in list
    db.execute("UPDATE cards SET priority_y = NULL WHERE event_id = ?", event_id)

    # Fetch two cards for the event - random until optimizing in the future
    cards = db.execute("""
        SELECT id, content FROM cards
        WHERE event_id = ? 
        ORDER BY RANDOM() LIMIT 2
    """, event_id)

    # Check if there are at least two items to compare
    if len(cards) < 2:
        return jsonify({"done": True})

    return jsonify({"item1": cards[0], "item2": cards[1]})


@app.route('/submit_comparison', methods=['POST'])
@login_required
def submit_comparison():
    """Prompt user to compare cards until there are no NULL or duplicate priorities."""
    data = request.get_json()
    event_id = data.get('event_id')
    chosen_content = data.get('chosen')
    other_content = data.get('other')

    # Fetches card data
    def fetch_card_data(content):
        query = """
            SELECT id, priority_y FROM cards WHERE content = ? AND event_id = ?
        """
        return db.execute(query, content, event_id)

    # Updates card priority
    def update_card_priority(card_id, priority):
        query = "UPDATE cards SET priority_y = ? WHERE id = ?"
        db.execute(query, priority, card_id)

    # Fetches cards without a priority
    def fetch_null_priority_cards():
        query = """
            SELECT id, content FROM cards
            WHERE event_id = ? AND priority_y IS NULL
        """
        return db.execute(query, event_id)

    # Fetches cards with the same priority
    def fetch_duplicate_cards():
        query = """
            SELECT id, content FROM cards
            WHERE event_id = ? AND priority_y IN (
                SELECT priority_y
                FROM cards
                WHERE event_id = ?
                GROUP BY priority_y
                HAVING COUNT(*) > 1
            )
            ORDER BY priority_y
        """
        return db.execute(query, event_id, event_id)

    # Fetches the next pair to compare
    def fetch_next_comparison_pair():
        null_cards = fetch_null_priority_cards()
        if null_cards:
            return null_cards[0], null_cards[1] if len(null_cards) > 1 else null_cards[0]

        duplicates = fetch_duplicate_cards()
        if duplicates and len(duplicates) > 1:
            return duplicates[0], duplicates[1]

        return None, None

    # Fetch chosen and not chosen cards
    chosen_card = fetch_card_data(chosen_content)
    other_card = fetch_card_data(other_content)

    # Updates the priority of cards compared
    if chosen_card and other_card:
        chosen_id = chosen_card[0]['id']
        other_id = other_card[0]['id']
        other_priority = other_card[0]['priority_y']

        if other_priority is not None:
            new_priority = other_priority - 1
            other_priority = new_priority + 1
        else:
            num_rows_query = "SELECT COUNT(*) FROM cards WHERE event_id = ?"
            num_rows = db.execute(num_rows_query, event_id)[0]['COUNT(*)']
            new_priority = num_rows - 1
            other_priority = new_priority + 1

        update_card_priority(chosen_id, new_priority)
        update_card_priority(other_id, other_priority)

    next_card1, next_card2 = fetch_next_comparison_pair()

    # Returns cards if there are null or duplicate priority cards
    if next_card1 and next_card2:
        return jsonify({"nextItem1": next_card1, "nextItem2": next_card2})

    return jsonify({"done": True})

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

