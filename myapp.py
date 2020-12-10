from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, ForeignKey
import sqlite3
import pandas as pd

app = Flask(__name__)

con = sqlite3.connect('guilty_pleasure.db')
cur = con.cursor()

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///guilty_pleasure.db'
db = SQLAlchemy(app)


quests = {
    '1':'songs',
    '2':'songs_freq',
    '3':'song_title',
    '4':'song_artist'
}
pd.DataFrame({'id': quests.keys(), 'question': quests.values()}).to_sql('questions', con, index = False, if_exists='replace')


class Questions(db.Model):
    __tablename__ = 'questions'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text)


cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT, 
    gender text,
    age int
)
""")
con.commit()


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    gender = db.Column(db.Text)
    age = db.Column(db.Integer)


cur.execute("""
CREATE TABLE IF NOT EXISTS answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id int, 
    question_id text,
    answer text
)
""")
con.commit()


class Answers(db.Model):
    __tablename__ = 'answers'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey('users.id'))
    question_id = db.Column(db.Integer, ForeignKey('questions.id'))
    answer = db.Column(db.Text)


@app.route('/')
def index():
    return render_template('index1.html')

@app.route('/survey', methods=["GET"])
def survey():
    return render_template('survey3.html')

@app.route('/process')
def done():
    if request.args:
        gender = request.args.get('gender')
        age = request.args.get('age')
        user = User(
            age=age,
            gender=gender,
        )
        db.session.add(user)
        db.session.commit()
        user_id = user.id

        songs = request.args.getlist('songs')
        for entry in songs:
            answer_song = Answers(user_id=user_id, question_id=1, answer=entry)
            db.session.add(answer_song)
            db.session.commit()

        songs_freq = request.args.get('songs_freq')
        answer_freq = Answers(user_id=user_id, question_id=2, answer=songs_freq)
        db.session.add(answer_freq)
        db.session.commit()

        song_title = request.args.get('song_title')
        answer_title = Answers(user_id=user_id, question_id=3, answer=song_title)
        db.session.add(answer_title)
        db.session.commit()

        song_artist = request.args.get('song_artist')
        answer_artist = Answers(user_id=user_id, question_id=4, answer=song_artist)
        db.session.add(answer_artist)
        db.session.commit()

    return render_template('process.html')

@app.route('/stats')
def stats():
    all_info = {}
    all_info['n_users'] = db.session.query(
        func.count(User.id)).one()[0]
    age_stats = db.session.query(
        func.avg(User.age),
        func.min(User.age),
        func.max(User.age)
    ).one()
    all_info['age_mean'] = age_stats[0]
    all_info['age_min'] = age_stats[1]
    all_info['age_max'] = age_stats[2]

    con = sqlite3.connect('guilty_pleasure.db')
    cur = con.cursor()
    query1 = '''SELECT 
        question_id,
        answer,
        COUNT(answer) as N_answers
    FROM answers
    WHERE question_id=1
    GROUP BY answer
    ORDER BY N_answers DESC'''
    cur.execute(query1)
    rating = list(cur.fetchall())
    all_info['rating'] = rating

    query2 = '''SELECT 
        question_id,
        answer,
        COUNT(answer) as N_answers
    FROM answers
    WHERE question_id=2
    GROUP BY answer
    ORDER BY N_answers DESC'''
    cur.execute(query2)
    freq = list(cur.fetchall())
    all_info['freq'] = freq

    query3 = '''SELECT 
        question_id,
        user_id,
        group_concat(answer) as title_artist
    FROM answers
    WHERE question_id=3 OR question_id=4
    GROUP BY user_id'''
    cur.execute(query3)
    recs = list(cur.fetchmany(10))
    all_info['recs'] = recs

    return render_template("stats1.html", all_info=all_info)

if __name__ == '__main__':
    app.run(debug=False)
