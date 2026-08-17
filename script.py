from flask import Flask, render_template_string, request, redirect, url_for, session
import sqlite3
import random

app = Flask(__name__)
app.secret_key = "adaptive_quiz_secret_key"

DATABASE = "adaptive_quiz.db"

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Adaptive Quiz Management System</title>

<style>
body {
    font-family: Arial;
    background: #dfefff;
    margin: 0;
}

.header {
    background: #1e3d59;
    color: white;
    padding: 25px;
    text-align: center;
    font-size: 28px;
    font-weight: bold;
}

.container {
    width: 80%;
    max-width: 900px;
    margin: 30px auto;
}

.box {
    background: white;
    padding: 30px;
    border-radius: 10px;
    box-shadow: 0 3px 10px #999;
    margin-bottom: 20px;
}

input[type=text] {
    padding: 12px;
    width: 250px;
    font-size: 16px;
}

button {
    padding: 12px 20px;
    background: #1e3d59;
    color: white;
    border: none;
    border-radius: 5px;
    font-size: 15px;
    cursor: pointer;
}

button:hover {
    background: #163047;
}

.option {
    display: block;
    background: #f2f2f2;
    padding: 15px;
    margin: 10px 0;
    border-radius: 5px;
    cursor: pointer;
}

.option:hover {
    background: #e0e0e0;
}

.info {
    display: flex;
    justify-content: space-between;
    font-size: 18px;
    font-weight: bold;
}

table {
    width: 100%;
    border-collapse: collapse;
}

th, td {
    padding: 12px;
    border: 1px solid #ccc;
    text-align: center;
}

th {
    background: #1e3d59;
    color: white;
}

.correct {
    color: green;
    font-weight: bold;
}

.wrong {
    color: red;
    font-weight: bold;
}
</style>
</head>

<body>

<div class="header">
Adaptive Quiz Management System
</div>

<div class="container">

{% if page == "login" %}

<div class="box">

<h2>Student Login</h2>

<form method="POST">

<label>Enter Username:</label>
<br><br>

<input type="text" name="username" required>

<br><br>

<button type="submit">
START QUIZ
</button>

</form>

</div>

{% elif page == "quiz" %}

<div class="box">

<div class="info">

<span>
Student: {{ username }}
</span>

<span>
Score: {{ score }}
</span>

<span>
Ability: {{ ability }}
</span>

</div>

</div>

<div class="box">

<h2>{{ question[1] }}</h2>

<form method="POST" action="/answer">

{% for option in options %}

<label class="option">

<input
type="radio"
name="answer"
value="{{ option }}"
required
>

{{ option }}

</label>

{% endfor %}

<br>

<button type="submit">
SUBMIT ANSWER
</button>

</form>

</div>

{% elif page == "result" %}

<div class="box">

<h2>Answer Result</h2>

{% if correct %}

<p class="correct">
Correct Answer!
</p>

{% else %}

<p class="wrong">
Wrong Answer!
</p>

<p>
Correct Answer:
<strong>{{ correct_answer }}</strong>
</p>

{% endif %}

<p>
Student Ability:
<strong>{{ ability }}</strong>
</p>

<p>
Score:
<strong>{{ score }}</strong>
</p>

<br>

<a href="/quiz">
<button>NEXT QUESTION</button>
</a>

</div>

{% elif page == "final" %}

<div class="box">

<h2>Quiz Result</h2>

<p>
Student:
<strong>{{ username }}</strong>
</p>

<p>
Final Score:
<strong>{{ score }}</strong>
</p>

<p>
Final Ability:
<strong>{{ ability }}</strong>
</p>

<form method="POST" action="/save">

<button type="submit">
SAVE SCORE
</button>

</form>

<br>

<a href="/leaderboard">
<button>LEADERBOARD</button>
</a>

<br><br>

<a href="/">
<button>NEW QUIZ</button>
</a>

</div>

{% elif page == "leaderboard" %}

<div class="box">

<h2>Leaderboard</h2>

<table>

<tr>
<th>Username</th>
<th>Score</th>
</tr>

{% for row in scores %}

<tr>
<td>{{ row[0] }}</td>
<td>{{ row[1] }}</td>
</tr>

{% endfor %}

</table>

<br>

<a href="/">
<button>NEW QUIZ</button>
</a>

</div>

{% endif %}

</div>

</body>
</html>
"""


def get_connection():
    return sqlite3.connect(DATABASE)


def setup_database():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT,
        option1 TEXT,
        option2 TEXT,
        option3 TEXT,
        option4 TEXT,
        correct_answer TEXT,
        difficulty REAL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        score INTEGER
    )
    """)

    cursor.execute("SELECT COUNT(*) FROM questions")

    count = cursor.fetchone()[0]

    if count == 0:

        questions = [
            (
                "2 + 2 = ?",
                "2",
                "3",
                "4",
                "5",
                "4",
                -2
            ),
            (
                "Capital of India?",
                "Delhi",
                "Mumbai",
                "Chennai",
                "Kolkata",
                "Delhi",
                -1
            ),
            (
                "Derivative of x^2?",
                "x",
                "2x",
                "x^2",
                "1",
                "2x",
                0
            ),
            (
                "Integral of 1/x?",
                "x",
                "ln(x)",
                "1/x^2",
                "0",
                "ln(x)",
                1
            ),
            (
                "Who proposed Relativity?",
                "Newton",
                "Einstein",
                "Tesla",
                "Bohr",
                "Einstein",
                0
            ),
            (
                "Solve ∫x sin(x) dx",
                "sin x",
                "-x cos x + sin x",
                "x sin x",
                "0",
                "-x cos x + sin x",
                2
            )
        ]

        cursor.executemany("""
        INSERT INTO questions
        (
            question,
            option1,
            option2,
            option3,
            option4,
            correct_answer,
            difficulty
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, questions)

    conn.commit()
    conn.close()


def get_question(ability):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT *
    FROM questions
    ORDER BY ABS(difficulty - ?)
    LIMIT 1
    """, (ability,))

    question = cursor.fetchone()

    conn.close()

    return question


@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"].strip()

        session.clear()

        session["username"] = username
        session["score"] = 0
        session["ability"] = 0
        session["questions_answered"] = 0
        session["current_question"] = None

        return redirect("/quiz")

    return render_template_string(
        HTML,
        page="login"
    )


@app.route("/quiz")
def quiz():

    if "username" not in session:
        return redirect("/")

    if session["questions_answered"] >= 6:
        return redirect("/final")

    ability = session["ability"]

    question = get_question(ability)

    if question is None:
        return "No questions found."

    options = [
        question[2],
        question[3],
        question[4],
        question[5]
    ]

    random.shuffle(options)

    session["current_question"] = question[0]

    return render_template_string(
        HTML,
        page="quiz",
        username=session["username"],
        score=session["score"],
        ability=round(session["ability"], 2),
        question=question,
        options=options
    )


@app.route("/answer", methods=["POST"])
def answer():

    if "username" not in session:
        return redirect("/")

    selected = request.form["answer"]

    question_id = session["current_question"]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM questions WHERE id = ?",
        (question_id,)
    )

    question = cursor.fetchone()

    conn.close()

    correct_answer = question[6]

    if selected == correct_answer:

        session["score"] += 1
        session["ability"] += 0.5

        correct = True

    else:

        session["ability"] -= 0.5

        correct = False

    session["questions_answered"] += 1

    return render_template_string(
        HTML,
        page="result",
        correct=correct,
        correct_answer=correct_answer,
        score=session["score"],
        ability=round(session["ability"], 2)
    )


@app.route("/final")
def final():

    if "username" not in session:
        return redirect("/")

    return render_template_string(
        HTML,
        page="final",
        username=session["username"],
        score=session["score"],
        ability=round(session["ability"], 2)
    )


@app.route("/save", methods=["POST"])
def save():

    if "username" not in session:
        return redirect("/")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO scores(username, score)
    VALUES (?, ?)
    """, (
        session["username"],
        session["score"]
    ))

    conn.commit()
    conn.close()

    return redirect("/leaderboard")


@app.route("/leaderboard")
def leaderboard():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT username, score
    FROM scores
    ORDER BY score DESC
    """)

    scores = cursor.fetchall()

    conn.close()

    return render_template_string(
        HTML,
        page="leaderboard",
        scores=scores
    )


if __name__ == "__main__":

    setup_database()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )