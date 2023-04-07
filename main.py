# NOTE:
# ** nullable = False**
# Problem ----when creating a new table, if the column parameters "nullable" set to "false", 
#               will have error if no data in column when you add a new record
# How to solve? -- set to True and delete exist db file , run code and create a new db file

from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField,FloatField
from wtforms.validators import DataRequired
import requests
import os
print(os.environ.get('API_KEY'))
print(os.environ.get('MY_SECRET_KEY'))
#      ----------------------     FETCH MOVIE DATAS FROM API      -------------------
MOVIE_DB_API_KEY =os.environ.get('API_KEY')
MOVIE_DB_SEARCH_URL= "https://api.themoviedb.org/3/search/movie"
MOVIE_DB_MOVIE_URL = "https://api.themoviedb.org/3/movie"
MOVIE_DB_IMAGE_URL =" https://image.tmdb.org/t/p/w500"


#    -------------                CREATE APP                 -----------------

app = Flask(__name__)
app.config['SECRET_KEY'] =os.environ.get('MY_SECRET_KEY')
Bootstrap(app)

#       --------------------------       CREATE DATABASEES          ----------------------
db = SQLAlchemy()
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///movie_list.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# initialize the app with the extension
db.init_app(app)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(250), unique = True, nullable = False)
    year = db.Column(db.Integer,  nullable = False)
    description = db.Column(db.String(500),  nullable = False)
    rating = db.Column(db.Float,  nullable = True)
    ranking = db.Column(db.Integer,nullable = True)
    review = db.Column(db.String(250),  nullable = True)
    img_url = db.Column(db.String(250),  nullable = False)

with app.app_context():
    db.create_all()

    # Test : add a new record (movie) 
    # new_movie = Movie(
    #     title="Phone Booth",
    #     year=2002,
    #     description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
    #     rating=7.3,
    #     ranking=10,
    #     review="My favourite character was the caller.",
    #     img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
    # )
    # db.session.add(new_movie)
    # db.session.commit()


#     ---------------------            CREATE FORM              ----------------------------------
class MovieRatingForm(FlaskForm):
    rating = FloatField(label="Your Rating out of 10 e.g.7.5", validators=[DataRequired()])
    review = StringField(label="Your Review")
    sumbit = SubmitField(label="Done")


class FindMovieForm(FlaskForm):
    title = StringField(label="Movie Title", validators=[DataRequired()])
    sumbit = SubmitField(label="Add Movie")






@app.route("/")
def home():
    # creates a list of all the movies sorted by rating
    all_movies = Movie.query.order_by(Movie.rating).all()
    # loop through all movies and update ranking by order
    for n in range(len(all_movies)):
        all_movies[n].ranking = len(all_movies)-n
    db.session.commit()
    return render_template("index.html", movies = all_movies)


@app.route("/edit", methods = ["GET","POST"])
def edit():
    form = MovieRatingForm()
    movie_id = request.args.get("id")
    movie_to_update = Movie.query.get(movie_id)
    if form.validate_on_submit():
        # Update record to database
        movie_to_update.rating = form.rating.data
        movie_to_update.review = form.review.data
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("edit.html", form = form)


@app.route("/delete")
def delete():
    movie_id = request.args.get("id")
    movie_to_delete = Movie.query.get(movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/search", methods=["GET","POST"])
def find_movie():
    form = FindMovieForm()
    if form.validate_on_submit():
        # fetch movie data from API 
        res = requests.get(MOVIE_DB_SEARCH_URL, params={"api_key" : MOVIE_DB_API_KEY,"query" : form.title.data})
        data = res.json()["results"]
        return render_template("select.html", options = data)

    return render_template("add.html", form= form)


@app.route("/add")
def add():
    # Fetch data from API
    movie_id = request.args.get("id")
    res = requests.get(f"{MOVIE_DB_MOVIE_URL}/{movie_id}", params = {"api_key": MOVIE_DB_API_KEY })
    data = res.json()
    # add new movie to databases table
    new_movie = Movie(
        title=data["original_title"],
        year= data["release_date"].split("-")[0],
        description=data["overview"],
        img_url= f"{MOVIE_DB_IMAGE_URL}{data['poster_path']}",
    )
    db.session.add(new_movie)
    db.session.commit()
    # need to pass the new movie record id to edit function, so the function will be able to find the new movie by id
    # eidt route endpoint should looks like" /edit?id=1"
    return redirect(url_for("edit", id = new_movie.id ))


if __name__ == '__main__':
    app.run(debug=True)
