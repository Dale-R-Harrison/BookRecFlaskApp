from app import db, login
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from hashlib import md5

@login.user_loader
def load_user(id):
    return Users.query.get(int(id))

recommended = db.Table('recommended_books',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('book_id', db.Integer, db.ForeignKey('books.id'))
)

reviewed = db.Table('reviewed_books',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('book_id', db.Integer, db.ForeignKey('books.id'))
)

class Books(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), index=True)
    author = db.Column(db.String(240), default='Unknown')
    isbn = db.Column(db.String(15))

    def __repr__(self):
        return 'Title {}, Author: {}'.format(self.title, self.author)

class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128), unique=True)
    recommended=db.relationship(
        'Books', secondary=recommended,
        primaryjoin=(recommended.c.user_id == id),
        secondaryjoin=(recommended.c.book_id == Books.id),
        backref=db.backref("recommendee", lazy='dynamic'), lazy='dynamic')
    reviewed=db.relationship(
        'Books', secondary=reviewed,
        primaryjoin=(reviewed.c.user_id == id),
        secondaryjoin=(reviewed.c.book_id == Books.id),
        backref=db.backref('reviewer', lazy='dynamic'), lazy='dynamic')


    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size
        )

    def recommend(self, book):
        if not self.is_recommended(book):
            self.recommended.append(book)

    def drop_recommend(self, book):
        if self.is_recommended(book):
            self.recommended.remove(book)

    def is_recommended(self, book):
        return self.recommended.filter(
            recommended.c.book_id == book.id).count() > 0

    def review(self, book):
        if not self.is_reviewed(book):
            self.reviewed.append(book)

    def is_reviewed(self, book):
        return self.reviewed.filter(
            reviewed.c.book_id == book.id).count() > 0
