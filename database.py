from flask import g
import sqlite3, os

    
basedir = os.path.abspath(os.path.dirname(__file__))
DB_NAME = os.path.join(basedir, 'faq.db')

def connect_db():
    sql = sqlite3.connect(DB_NAME)
    sql.row_factory = sqlite3.Row
    return sql


def get_db():
    if not hasattr(g, DB_NAME):
        g.sqlite_db = connect_db()
    return g.sqlite_db