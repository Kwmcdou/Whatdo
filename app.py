import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


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
    """Show portfolio of stocks"""

    # Get user cash from db
    cashResults = db.execute(
        "SELECT cash FROM users WHERE id = ?", session["user_id"]
    )
    cash = cashResults[0]["cash"]

    # Get user stocks form db
    stockResults = db.execute(
        "SELECT *, SUM(shares) AS [total_shares] FROM stocks WHERE user_id = ? GROUP BY symbol", session["user_id"]
    )

    # Total and format user data
    total = 0
    for stock in stockResults:
        quote = lookup(stock["symbol"])
        if quote:
            stock["current_price"] = quote["price"]
            price = stock["current_price"]
            total += stock["shares"] * price
            stock["value"] = stock["total_shares"] * price

            # Format current_price and value using usd function
            stock["current_price"] = usd(stock["current_price"])
            stock["value"] = usd(stock["value"])

    # Update total to assets + cash
    total += cash

    # Format cash and total using usd function
    cash = usd(cash)
    total = usd(total)

    return render_template("index.html", cash=cash, stocks=stockResults, total=total)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    # Purchase stock so long as the user can afford it
    if request.method == "POST":

        # Get symbol input from form
        symbol = request.form.get("symbol")
        symbol = symbol.upper()
        if not symbol:
            return apology("please enter a stock symbol", 400)

        # Get shares input from form
        shares = request.form.get("shares")

        # Ensure shares was submitted
        if not shares:
            return apology("please enter the number of shares", 400)

        # Ensure shares is a digit
        if not shares.isdigit():
            return apology("please enter a valid number of shares", 400)

        # Ensure shares is greater than 0
        if not int(shares) > 0:
            return apology("please enter a valid number of shares", 400)

        # Lookup quote for symbol
        quote_results = lookup(symbol)
        if quote_results == None:
            return apology("stock symbol not found", 400)

        # Calculate total cost (price * shares)
        cost = int(quote_results["price"]) * int(request.form.get("shares"))

        # Check if user has cash available for purchase
        cash = db.execute(
            "SELECT cash FROM users WHERE id = ?", session["user_id"]
        )
        available = cash[0]["cash"]
        remaining = available - cost

        if remaining < 0:
            return apology("not enough cash", 400)

        # Update cash remaining after purchase
        db.execute(
            "UPDATE users SET cash = ? WHERE id = ?", remaining, session["user_id"]
        )

        # Update user's stocks after purchase
        db.execute(
            "INSERT INTO stocks (symbol, shares, amount, user_id, transaction_type) VALUES (?, ?, ?, ?, ?)", symbol, shares, quote_results[
                "price"], session["user_id"], 'buy'
        )

        return redirect("/")

    # Render buy page
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    # Get user stocks from db
    stocks = db.execute(
        "SELECT symbol, shares, amount, timestamp, transaction_type FROM stocks WHERE user_id = ? ORDER BY timestamp DESC", session[
            "user_id"]
    )

    # Format amount as usd
    for stock in stocks:
        stock["amount"] = usd(stock["amount"])

    return render_template("history.html", stocks=stocks)


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


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":

        # Validate stock symbol input
        if not request.form.get("symbol"):
            return apology("must provide valid stock symbol", 400)

        # Lookup stock symbol
        quote_results = lookup(request.form.get("symbol"))

        # Validate lookup response is not none
        if quote_results == None:
            return apology("stock symbol not found", 400)

        # Format price as USD
        quote_results["price"] = usd(quote_results["price"])

        # Display quote results
        return render_template("quote.html", name=quote_results["name"], price=quote_results["price"], symbol=quote_results["symbol"])

    else:
        return render_template("quote.html")


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


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    # Sell stock so long as the user has shares to sell
    if request.method == "POST":

        # Get symbol from form
        symbol = request.form.get("symbol")
        symbol = symbol.upper()

        # Check that symbol was submitted
        if not symbol:
            return apology("please enter a stock symbol", 400)

        # Get user's stocks from db
        stocks = db.execute(
            "SELECT *, SUM(shares) AS [total_shares] FROM stocks WHERE user_id = ? GROUP BY symbol", session["user_id"]
        )

        # Get shares from form
        shares = request.form.get("shares")

        # Check that shares was submitted
        if not shares:
            return apology("please enter the number of shares", 400)

        # Check that user has stocks and amount to sell
        for stock in stocks:
            if stock["symbol"] == symbol and stock["total_shares"] < int(shares):
                return apology("not enough shares to sell", 400)

        # Format shares as negative(credit) for the stocks db
        shares = int(shares)
        shares = shares * (-1)

        # Lookup current price of stock for sale
        quote_results = lookup(symbol)
        if quote_results == None:
            return apology("stock symbol not found", 400)

        # Calculate the total credit for sale (shares * price)
        credit = int(quote_results["price"]) * int(request.form.get("shares"))

        # Get user's current cash balance from the db
        cash = db.execute(
            "SELECT cash FROM users WHERE id = ?", session["user_id"]
        )
        cash = cash[0]["cash"]
        # Calculate balance after transaction
        balance = cash + credit

        # Update user's cash to reflect the new balance
        db.execute(
            "UPDATE users SET cash = ? WHERE id = ?", balance, session["user_id"]
        )

        # Update user's stocks leger with new transaction
        db.execute(
            "INSERT INTO stocks (symbol, shares, amount, user_id, transaction_type) VALUES (?, ?, ?, ?, ?)", symbol, shares, quote_results[
                "price"], session["user_id"], 'sell'
        )

        return redirect("/")

    else:
        # Get user's stocks to populate options for the select element
        stocks = db.execute(
            "SELECT *, SUM(shares) AS [total_shares] FROM stocks WHERE user_id = ? GROUP BY symbol", session["user_id"]
        )

        return render_template("sell.html", stocks=stocks)
