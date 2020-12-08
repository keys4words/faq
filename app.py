from flask import Flask, render_template, g, request, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash

from database import get_db
import os


app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)


################
@app.teardown_appcontext
def close_db(error):
    # if hasattr(g, 'sqlite_db'):
    #     g.sqlite_db.close()
    if hasattr(g, 'postgres_db_conn'):
        g.postgres_db_conn.close()

    if hasattr(g, 'postgres_db_cur'):
        g.postgres_db_cur.close()


def get_current_user():
    res = None
    if 'user' in session:
        db = get_db()
        # user_cur = db.execute('select * from users where name = ?', [session['user']])
        # res = user_cur.fetchone()
        db.execute('select * from users where name = %s', (session['user'],))
        res = db.fetchone()
    
    return res


@app.route('/')
def home():
    user = get_current_user()

    db = get_db()
    # questions_cur = db.execute('''select questions.id
    #                                     as question_id
    #                                 , questions.question_text 
    #                                 , askers.name
    #                                     as asker_name
    #                                 , experts.name
    #                                     as expert_name
    #                             from questions 
    #                             join users as askers 
    #                                 on askers.id = questions.asked_by_id 
    #                             join users as experts
    #                                  on experts.id = questions.expert_id
    #                             where questions.answer_text is not null''')
    db.execute('''select questions.id as question_id
                                    , questions.question_text 
                                    , askers.name as asker_name
                                    , experts.name as expert_name
                                from questions 
                                join users as askers 
                                    on askers.id = questions.asked_by_id 
                                join users as experts
                                     on experts.id = questions.expert_id
                                where questions.answer_text is not null''')
    
    # questions_res = questions_cur.fetchall()
    questions_res = db.fetchall()

    return render_template('home.html', user=user, questions=questions_res)


@app.route('/register', methods=['GET', 'POST'])
def register():
    user = get_current_user()

    if request.method == 'POST':
        db = get_db()
        # existing_user_cur = db.execute('select id from users where name = ?', [request.form['inputName']])
        db.execute('select id from users where name = %s', (request.form['inputName'], ))
        # existing_user = existing_user_cur.fetchone()
        existing_user = db.fetchone()

        if existing_user:
            return render_template('register.html', user=user, error='User already exists!')

        hashed_pass = generate_password_hash(request.form["inputPassword"], method='sha256')
        # db.execute('insert into users(name, password, expert, admin) values(?, ?, ?, ?)', [request.form["inputName"], hashed_pass, '0', '0'])
        db.execute('insert into users(name, password, expert, admin) values(%s, %s, %s, %s)', (request.form["inputName"], hashed_pass, '0', '0'))
        # db.commit()
        session['user'] = request.form['inputName']
        return redirect(url_for('home'))
    return render_template('register.html', user=user)


@app.route('/login', methods=['GET', 'POST'])
def login():
    user = get_current_user()
    error = None

    if request.method == 'POST':
        db = get_db()
        name = request.form["inputName"]
        password = request.form["inputPassword"]
        # user_cur = db.execute('select id, name, password from users where name = ?', [name])
        db.execute('select id, name, password from users where name = %s', (name, ))
        # user_result = user_cur.fetchone()
        user_result = db.fetchone()
        
        if user_result:
            if check_password_hash(user_result['password'], password):
                session['user'] = user_result['name']
                return redirect(url_for('home'))
            else:
                error = 'Wrong password'
        else:
            error = 'Wrong username'
        
    return render_template('login.html', user=user, error=error)


@app.route('/question/<question_id>', methods=['GET', 'POST'])
def question(question_id):
    user = get_current_user()
    db = get_db()
    # question_cur = db.execute('''select questions.question_text 
    #                                 , questions.answer_text
    #                                 , askers.name
    #                                     as asker_name
    #                                 , experts.name
    #                                     as expert_name
    #                             from questions 
    #                             join users as askers 
    #                                 on askers.id = questions.asked_by_id 
    #                             join users as experts
    #                                  on experts.id = questions.expert_id
    #                             where questions.id = ?''', [question_id])
    db.execute('''select questions.question_text 
                                    , questions.answer_text
                                    , askers.name as asker_name
                                    , experts.name as expert_name
                                from questions 
                                join users as askers 
                                    on askers.id = questions.asked_by_id 
                                join users as experts
                                     on experts.id = questions.expert_id
                                where questions.id = %s''', (question_id,))
    # question = question_cur.fetchone()
    question = db.fetchone()

    return render_template('question.html', user=user, question=question)


@app.route('/answer/<question_id>', methods=['GET', 'POST'])
def answer(question_id):
    user = get_current_user()

    if not user:
        return redirect(url_for('login'))

    if not user['expert']:
        return redirect(url_for('home'))

    db = get_db()
    if request.method == 'POST':
        # db.execute('update questions set answer_text = ? where id = ?', [request.form['answer'], question_id])
        db.execute('update questions set answer_text = %s where id = %s', (request.form['answer'], question_id))
        # db.commit()
        return redirect(url_for('unanswered'))
    # question_cur = db.execute('select id, question_text from questions where id = ?', [question_id])
    db.execute('select id, question_text from questions where id = %s', (question_id, ))
    # question = question_cur.fetchone()
    question = db.fetchone()
    return render_template('answer.html', user=user, question=question)


@app.route('/ask', methods=['POST', 'GET'])
def ask():
    user = get_current_user()

    if not user:
        return redirect(url_for('login'))

    db = get_db()

    if request.method == 'POST':
        question_text = request.form["question"]
        expert_id = request.form["expert"]
        # db.execute('insert into questions (question_text, asked_by_id, expert_id) values(?, ?, ?)', [question_text, user['id'], expert_id])
        db.execute('insert into questions (question_text, asked_by_id, expert_id) values(%s, %s, %s)', (question_text, user['id'], expert_id))
        # db.commit()
        return redirect(url_for('home'))
        
    # expert_cur = db.execute('select id, name from users where expert = 1')
    db.execute('select id, name from users where expert = True')
    # expert_res = expert_cur.fetchall()
    expert_res = db.fetchall()

    return render_template('ask.html', user=user, experts=expert_res)


@app.route('/unanswered')
def unanswered():
    user = get_current_user()

    if not user:
        return redirect(url_for('login'))

    # if user['expert'] == 0:
    if not user['expert']:
        return redirect(url_for('home'))

    db = get_db()
    # questions_cur = db.execute('''select questions.id
    #                                     ,questions.question_text
    #                                     ,questions.asked_by_id
    #                                     ,users.name
    #                             from questions
    #                             join users on users.id = questions.asked_by_id
    #                             where questions.answer_text is null and questions.expert_id = ?'''
    #                             , [user['id']])
    db.execute('''select questions.id
                        ,questions.question_text
                        ,questions.asked_by_id
                        ,users.name
                                from questions
                                join users on users.id = questions.asked_by_id
                                where questions.answer_text is null and questions.expert_id = %s'''
                                , (user['id'], ))
    # questions_res = questions_cur.fetchall()
    questions_res = db.fetchall()

    return render_template('unanswered.html', user=user, questions=questions_res)

@app.route('/users')
def users():
    user = get_current_user()

    if not user:
        return redirect(url_for('login'))

    # if user['admin'] == 0:
    if not user['admin']:
        return redirect(url_for('home'))

    db = get_db()
    # users_cur = db.execute('select id, name, expert, admin from users')
    db.execute('select id, name, expert, admin from users')
    # users_res = users_cur.fetchall()
    users_res = db.fetchall()

    return render_template('users.html', user=user, users=users_res)


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))


@app.route('/promote/<int:user_id>')
def promote(user_id):
    user = get_current_user()

    if not user:
        return redirect(url_for('login'))
    
    # if user['admin'] == 0:
    if not user['admin']:
        return redirect(url_for('home'))

    db = get_db()
    # db.execute('update users set expert = 1 where id = ?', [user_id])
    db.execute('update users set expert = True where id = %s', (user_id, ))
    # db.commit()
    return redirect(url_for('users'))






if __name__ == "__main__":
    app.run(debug=True)