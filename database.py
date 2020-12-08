from flask import g
import sqlite3, os
import psycopg2
from psycopg2.extras import DictCursor

    
# basedir = os.path.abspath(os.path.dirname(__file__))
# DB_NAME = os.path.join(basedir, 'faq.db')

# def connect_db():
#     sql = sqlite3.connect(DB_NAME)
#     sql.row_factory = sqlite3.Row
#     return sql

# def get_db():
#     if not hasattr(g, DB_NAME):
#         g.sqlite_db = connect_db()
#     return g.sqlite_db


def connect_db():
    conn = psycopg2.connect('postgres://gaomxkcfnvpkry:ab0be37d87b611f7c639f6667a6cab567b2a8e10ade63686050c87d29d9bf9f0@ec2-54-205-26-79.compute-1.amazonaws.com:5432/d3dgk60efcd2l2', cursor_factory=DictCursor)
    conn.autocommit = True
    sql = conn.cursor()
    return conn, sql

def get_db():
    db = connect_db()
    if not hasattr(g, 'postgres_db_conn'):
        g.postgres_db_conn = db[0]
    if not hasattr(g, 'postgres_db_cur'):
        g.postgres_db_cur = db[1]

    return g.postgres_db_cur


def init_db():
    db = connect_db()
    db[1].execute(open('schema.sql', 'r').read())
    db[1].close()
    db[0].close()


def init_admin():
    db = connect_db()
    db[1].execute('update users set admin = True where name = %s', ('admin',))
    db[1].close()
    db[0].close()