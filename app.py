from flask import Flask, render_template, g, request, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash

from database import get_db
import os


app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)


################
@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

def get_current_user():
    res = None
    if 'user' in session:
        db = get_db()
        user_cur = db.execute('select * from users where name = ?', [session['user']])
        res = user_cur.fetchone()
    
    return res


@app.route('/')
def home():
    # user = None
    # if 'user' in session:
    #     user = session['user']
    user = get_current_user()
    return render_template('home.html', user=user)


@app.route('/register', methods=['GET', 'POST'])
def register():
    user = get_current_user()

    if request.method == 'POST':
        db = get_db()
        hashed_pass = generate_password_hash(request.form["inputPassword"], method='sha256')
        db.execute('insert into users(name, password, expert, admin) values(?, ?, ?, ?)', [request.form["inputName"], hashed_pass, '0', '0'])
        db.commit()
        session['user'] = request.form['name']
        return redirect(url_for('home'))
    return render_template('register.html', user=user)


@app.route('/login', methods=['GET', 'POST'])
def login():
    user = get_current_user()

    if request.method == 'POST':
        db = get_db()
        name = request.form["inputName"]
        password = request.form["inputPassword"]
        user_cur = db.execute('select id, name, password from users where name = ?', [name])
        user_result = user_cur.fetchone()
        if user_result:
            if check_password_hash(user_result['password'], password):
                session['user'] = user_result['name']
                return redirect(url_for('home'))
            else:
                return 'Wrong password'
        else:
            return '<h1>There is no user with this name</h1>'
        
        return f'<h1>User {user_result["name"]} from db</h1>'
    return render_template('login.html', user=user)


@app.route('/question')
def question():
    user = get_current_user()

    return render_template('question.html', user=user)


@app.route('/answer')
def answer():
    user = get_current_user()

    return render_template('answer.html', user=user)


@app.route('/ask')
def ask():
    user = get_current_user()

    return render_template('ask.html', user=user)


@app.route('/unanswered')
def unanswered():
    user = get_current_user()

    return render_template('ananswered.html', user=user)

@app.route('/users')
def users():
    user = get_current_user()
    db = get_db()
    users_cur = db.execute('select id, name, expert, admin from users')
    users_res = users_cur.fetchall()

    return render_template('users.html', user=user, users=users_res)


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))


@app.route('/promote/<int:user_id>')
def promote(user_id):
    db = get_db()
    db.execute('update users set expert = 1 where id = ?', [user_id])
    db.commit()
    return redirect(url_for('users'))






if __name__ == "__main__":
    app.run(debug=True)