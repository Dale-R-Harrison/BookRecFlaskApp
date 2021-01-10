import os

class Config(object):
    SECRET_KEY = 'you will never guess'
    SQLALCHEMY_DATABASE_URI = 'postgres+psycopg2://postgres:Kingcarnie1@/postgres?host=/cloudsql/tidal-run-298508:us-west3:capstone-database'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CONN_MAX_AGE = None
    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = 1
    MAIL_USERNAME = 'vitusavitus@gmail.com'
    MAIL_PASSWORD = 'Kingcarnie'
    ADMINS = ['dhar471@wgu.edu']
