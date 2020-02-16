import os

from flask import Flask, session, render_template
from flask import request, jsonify, flash, redirect
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_bootstrap import Bootstrap

from service import book_service, review_service, user_service
from utils import get_goodreads_review

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

Bootstrap(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

@app.route("/")
def index():
    if "user_id" in session:
        return redirect("/books")
    return render_template("index.html")

@app.route("/sign_in", methods=["get", "post"])
def sign_in():
    if request.method.lower() == "post":
        username = request.form['username']
        password = request.form['password']
        user = user_service(db).get_user(username, password)
        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect("/books")
    return render_template("sign_in.html")

@app.route("/sign_up", methods=["get", "post"])
def sign_up():
    if request.method.lower() == "post":
        username = request.form['username']
        password = request.form['password']
        user_id = user_service(db).create_user(username, password)
        if user_id:
            session["user_id"] = user_id
            session["username"] = username
            return redirect("/books")
    return render_template("sign_up.html")

@app.route("/sign_out")
def sign_out():
    if "user_id" in session:
        session.pop('user_id')
    if "username" in session:
        session.pop('username')    
    return redirect("/")

@app.route("/books", methods=["get"])
def books():
    if "user_id" not in session:
        return redirect("/sign_in")
    page_num = request.values.get("page_num") if request.values.get("page_num") else 1
    per_page = request.values.get("per_page") if request.values.get("per_page") else 20
    keyword = request.values.get("keyword")
    try:
        page_num = int(page_num)
        per_page = int(per_page)
    except Exception:
        page_num = 1
        per_page = 20
    total_pages = book_service(db).count_page_numbers(per_page, keyword=keyword)
    if page_num > total_pages:
        return redirect("/books?page_num=1")
    books= book_service(db).get_books(page_num, per_page, keyword=keyword)
    data = []
    while books:
        if len(books) > 3:
            data.append(books[:4])
            books = books[4:]
        else:
            data.append(books)
            books = None
    return render_template("books.html", data=data, total_pages=total_pages, current_page=page_num)

@app.route("/book/<isbn>")
def book(isbn):
    if "user_id" not in session:
        return redirect("/sign_in")
    book = book_service(db).get_book_by_isbn(isbn)
    if not book:
        return render_template("error.html", message="Page does not exist.")
    goodreads_data = get_goodreads_review(isbn)
    book["work_ratings_count"] = goodreads_data[isbn]["work_ratings_count"]
    book["work_average_rating"] = goodreads_data[isbn]["average_rating"]
    book["reviews"] = review_service(db).get_reviews_by_book(book["id"])
    return render_template("book.html", book=book)

@app.route("/review", methods=["post"])
def review():
    if "user_id" not in session:
        return redirect("/sign_in")
    score = request.form['score-input']
    comment = request.form['comment-input']
    book_isbn = request.form['book-isbn']
    book = book_service(db).get_book_by_isbn(book_isbn)
    user_id = request.form['user-id']
    check_repeat = review_service(db).check_review(user_id, book["id"])
    if check_repeat:
        flash('It cannot be able to submit multiple reviews for the same book. Your old review will be raplaced.', "error")
        review_service(db).update_review(user_id, book["id"], score, comment)
    else:
        flash('Add new review success.', "success")
        review_service(db).create_review(user_id, book["id"], score, comment)
    return redirect("/book/{0}".format(book_isbn))

@app.route("/api/<isbn>")
def api(isbn):
    book = book_service(db).get_book_detail(isbn)
    return jsonify(book)

@app.errorhandler(404)
def handle_404(self):
    return render_template("error.html", message="Page does not exist.")

@app.errorhandler(500)
def handle_500(self):
    return render_template("error.html", message="An error occurred inside the program.")

if __name__ == "__main__":
    app.run(port=5000)
