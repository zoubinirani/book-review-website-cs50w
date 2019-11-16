import os

from flask import Flask, render_template, jsonify, request, render_template, flash, session, abort
from flask_session import Session
from sqlalchemy import create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker
from passlib.hash import pbkdf2_sha256
from time import sleep
import requests

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

#main page
@app.route("/")
def index():
    return render_template("index.html", Sess = session)

#registration page
@app.route("/registration")
def registration():
    if session.get("username") is not None:
        session["username"] = None
    return render_template("registration.html")

@app.route("/signup", methods=["POST"]) 
def signup():

    # Information received from registration form
    email = request.form.get("email")
    password = request.form.get("password")
    confirmpassword = request.form.get("confirmpassword")

    if len(password) < 6:
        flash('Please select a password with a longer length (length at least 6!)')
        return render_template("registration.html")
    
    #try to query email: if it appears render_template to signup so they can try again
    num_accts = db.execute("SELECT * from users WHERE id = :email", {"email":email}).fetchone() 

    if num_accts is not None:
        flash('Email address is already taken, please select another one!')
        return render_template("registration.html")

    #encode password
    password = pbkdf2_sha256.hash(password)

    #check if passwords do not match
    if not pbkdf2_sha256.verify(confirmpassword, password):
        flash("Passwords do not match! Please try again!")
        return render_template("registration.html")

    #encode and insert
    confirmpassword = pbkdf2_sha256.hash(confirmpassword) #overwrite confirmpassword

    db.execute("INSERT INTO users (id, password) VALUES (:email, :password)", {"email":email, "password":password})
    db.commit()
    
    flash("You have now signed up! Please login!")
    return render_template("login.html")

#login page
@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/logout")
def logout():
    if session.get("username") is not None:
        session["username"] = None
    return render_template("index.html", Sess = session)

@app.route("/logged_status", methods=["POST"])
def logged_status():
    
    # Information received from login form
    email = request.form.get("email")
    password = request.form.get("password")

    #try to query email: if it appears render_template to signup so they can try again
    hash_password = db.execute("SELECT password from users WHERE id = :email", {"email":email}).fetchone() 

    if hash_password is None:
        flash("Email does not exist... try again!...")
        return render_template("login.html")

    if pbkdf2_sha256.verify(password, hash_password[0]):
        flash("Successfully logged in!...")
        if session.get("username") is None:
            session["username"] = email
        return render_template("index.html", Sess = session)
    
    flash('Password is incorrect! Try again!')
    return render_template("login.html")

@app.route("/search")
def search():
    if session.get("username") is None:
        flash('You need to login!')
        return render_template("index.html", Sess = session)
    return render_template("search.html")

@app.route("/search_book", methods = ["POST"])
def search_book():
    
    # Information received from search form
    title = request.form.get("title")
    author = request.form.get("author")
    isbn = request.form.get("isbn")

    #Returns all search results
    results = db.execute(text("""SELECT * from books WHERE (
    (isbn LIKE ('%' || :isbn || '%') OR :isbn is null) 
    AND (author LIKE ('%' || :author || '%') OR :author is null)
    AND (title LIKE ('%' || :title || '%') OR :title is null))
    """), {"isbn": isbn,"author": author,"title": title}).fetchall()

    if results:
        return render_template("search_results.html", results=results)
    flash("No search results...please try again!")
    return render_template("search.html")

@app.route("/search_results")
def search_results(results):
    return (render_template("search_results.html", results=results))

@app.route("/book/<string:book_isbn>")
def book(book_isbn):
    isbn = book_isbn

    #Get data from DataBase
    result = db.execute(text("SELECT * from books WHERE isbn =:isbn"), {"isbn": isbn}).fetchone()

    isbns = result.isbn

    #Get data from GoodReads API
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "ytMANoLD9Gxs2g7LGR9mcg", "isbns": isbns})

    #Get reviews data
    reviews = db.execute(text("SELECT * from reviews WHERE isbn =:isbn"), {"isbn": isbn}).fetchall()
    
    goodreads_rating = res.json()["books"][0]['average_rating']
    goodreads_ratings_count = res.json()["books"][0]['work_ratings_count']

    return render_template("book.html", result=result, rating=goodreads_rating, count = goodreads_ratings_count, reviews=reviews)

@app.route("/book/<string:book_isbn>/write_review", methods = ["POST"])
def write_review(book_isbn):
    review = request.form.get("review")
    user_id = session.get("username")
    isbn = book_isbn
    try:
        review_exists = db.execute(text("SELECT * from reviews WHERE isbn =:isbn AND user_id =:user_id"), {"isbn": isbn, "user_id": user_id}).fetchone()
        if review_exists:
            db.execute(text("UPDATE reviews SET review=:review WHERE isbn =:isbn AND user_id =:user_id"), {"review": review, "isbn": isbn, "user_id": user_id})
            db.commit()
        else:
            db.execute("""INSERT INTO reviews (review, user_id, isbn) VALUES (:review, :user_id, :isbn)""", 
            {"review":review, "user_id":user_id, "isbn":isbn})
            db.commit()
    except:
        pass
    
    db.commit()

    return book(book_isbn)

@app.route("/api/<string:isbn>/", methods = ["GET"])
def get_book_data(isbn):
    internal_data = db.execute(text("SELECT * from books WHERE isbn =:isbn"), {"isbn": isbn}).fetchone()
    
    #Return 404 response if not available
    if not internal_data: 
        return abort(404)

    #Get data from GoodReads API
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "ytMANoLD9Gxs2g7LGR9mcg", "isbns": isbn})

    goodreads_rating = res.json()["books"][0]['average_rating']
    goodreads_ratings_count = res.json()["books"][0]['work_ratings_count']

    return jsonify(title=internal_data.title,
                   author=internal_data.author,
                   year=internal_data.year,
                   isbn=internal_data.isbn,
                   review_count=goodreads_ratings_count,
                   average_score=goodreads_rating)
