from app import app, db
from flask import render_template, flash, redirect, url_for, request, send_file
from app.forms import LogInForm, RegistrationForm, ReviewForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import Users, Books
from werkzeug.urls import url_parse
from sqlalchemy import func
from scipy.sparse import csr_matrix
from io import BytesIO
import pandas as pd
import numpy as np
import glob as glob
import pickle
import matplotlib.pyplot as plt
from sklearn import preprocessing
from sklearn import model_selection
from sklearn.decomposition import TruncatedSVD
from sklearn.neighbors import NearestNeighbors
from scipy.sparse.linalg import svds

# All book reviewing and recommendation is generated from the web app Index
# Viewer will see form with book title and author and asked if they like the books
@app.route('/')
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    # read in the neccessary models created in jupyter notebook for use in the app
    with open('objs.pkl', 'rb') as f:
        title_list, corr, books_matrix = pickle.load(f)
    with open('kmodel.pkl', 'rb') as f:
        model_knn, user_matrix = pickle.load(f)
    # Query a random book to display to user
    book = Books.query.order_by(func.random()).first()
    query_index = pd.Index(user_matrix.index).get_loc(book.title)
    form = ReviewForm()
    # The following code uses the submitted form to recommend books if the book is liked
    if form.validate_on_submit():
        i = 0
        current_user.review(book)
        db.session.commit()
        rating = form.review.data
        if rating == 'Yes':
            titles = books_matrix.columns
            rec = title_list.index(book.title)
            corr_rec = corr[rec]
            recs = list(titles[(corr_rec >= 0.90)])
            # Sometime the above finds no books with an acceptable distribution
            # In this case, less accurate k-neighbors is used
            if len(recs) < 2:
                    # returns title ordered by distance form book referrred to by query_index
                    distances, indices = model_knn.kneighbors(
                        csr_matrix(user_matrix.iloc[query_index, :]).reshape(1, -1), n_neighbors = 6)
                    # adds books matching titles in rec list to recommended
                    for i in range(1, len(distances.flatten())):
                        rec_title = user_matrix.index[indices.flatten()[i]]
                        newbook = Books.query.filter_by(title=book.title).first()
                        current_user.recommend(newbook)
            for recbook in recs:
                if i > 5:
                    break
                newbook = Books.query.filter_by(title=recbook).first()
                current_user.recommend(newbook)
                i += 1
            db.session.commit()
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('index.html', title='Home', book=book, form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LogInForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or pasword')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/dash')
@login_required
def dash():
    users = Users.query.all()
    users.sort(key=lambda x: len(x.reviewed.all()), reverse=True)
    users = users[:5]
    return render_template('dash.html', title='Dashboard', users=users)

@app.route('/fig')
@login_required
def fig():
    books = Books.query.all()
    books.sort(key=lambda x: len(x.reviewer.all()), reverse = True)
    books = books[:3]

    bookdf = pd.DataFrame(columns=['Title', 'Reviews'])
    for book in books:
        df = pd.DataFrame([[book.title, len(book.reviewer.all())]], columns=['Title', 'Reviews'])
        bookdf = bookdf.append(df, ignore_index=True)

    fig, ax = plt.subplots(figsize=(10, 6))

    bar = ax.bar(x=bookdf['Title'], height=bookdf["Reviews"])

    # Customize the plot
    ax.set(title="Top 3 Books Reviewed by Users",
        xlabel="Book Title",
        ylabel="Number of Reviews");

    image = BytesIO()
    fig.savefig(image)
    image.seek(0)
    return send_file(image, mimetype='image/png')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = Users(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations! You are now a registered user.')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/user/<username>')
@login_required
def user(username):
    user = Users.query.filter_by(username=username).first_or_404()
    reclist = user.recommended.all()

    return render_template('user.html', user=user, reclist=reclist)
