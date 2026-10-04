from flask import Flask, render_template, redirect, request, session, flash, url_for, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from secrets import token_hex

from logic import integer, number, days_between, percentage, analyse_subject, analyse_overall, calculate_advice
from database import get_db

app = Flask(__name__)
app.permanent_session_lifetime = 604800
app.secret_key = token_hex(32)


@app.route("/")
def home():
    user_id = session.get('user_id')    # retrieves user id from session

    if not user_id:
        return redirect(url_for("login"))

    # open db
    connection = get_db()
    cursor = connection.cursor()

    # finds username based on user id in db
    cursor.execute('SELECT username FROM users WHERE user_id=?', (user_id,))
    user = cursor.fetchone()

    # manages non existant users
    if user is None:
        connection.close()
        return logout()

    # finds user subjects info
    command = """SELECT user_subjects.user_subject_id, 
                        subjects.subject_name, 
                        subjects.subject_id,
                        subjects.level, 
                        subjects.total_topics, 
                        user_subjects.target_grade 
                FROM user_subjects JOIN subjects 
                        ON user_subjects.subject_id=subjects.subject_id 
                WHERE user_subjects.user_id=?"""
    
    cursor.execute(command, (user_id,))
    user_subjects = cursor.fetchall()  

    connection.close()

    # Overall subject stats and pg calculation
    subject_means = []
    predicted_grades = []

    for subject in user_subjects:
            
        connection = get_db()
        cursor = connection.cursor()

        cursor.execute(
            """SELECT * FROM assessments
            WHERE user_subject_id=?
            ORDER BY assessment_date""",
            (subject["user_subject_id"],)
        )

        assessments = cursor.fetchall()
        connection.close()

        subject_analysis = analyse_subject(assessments, 
                                           subject["total_topics"],
                                           get_boundaries(subject["subject_id"], 2025, "May"))

        if subject_analysis["mean"] != "N/A":
            subject_means.append(subject_analysis["mean"])

        predicted_grades.append(subject_analysis["predicted_grade"])

    overall_analysis = analyse_overall(subject_means, predicted_grades)

    return render_template('index.html', username=user["username"], user_subjects=user_subjects, subjects=get_subjects(), overall_analysis=overall_analysis)

@app.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        # access the submitted values
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        # validates the values
        if not username or not password:
            flash('Undefined username or password')
            return redirect(url_for("register"))
        if len(password) < 8:
            flash('The password length should be at least 8 characters')
            return redirect(url_for("register"))

        # connect to database
        connection = get_db()

        cursor = connection.cursor()
        cursor.execute('SELECT user_id FROM users WHERE username=?', (username,))    # Check if username already exists
        user = cursor.fetchone()

        if user is not None:
            # the username already exists, showcases error
            flash('This username is already taken, choose another')
            connection.close()  # closes connection to db
            return redirect(url_for("register"))

        # password hashing
        password_hash = generate_password_hash(password)
        
        # The username doesn't exist in the database, can be inserted
        cursor.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, password_hash))
        connection.commit()
        connection.close()
        return redirect(url_for("login"))   # after registration redirects to login 
    
    return render_template('register.html')

@app.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        # access the submitted values and connects to database
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        connection = get_db()

        # Find user with the given entries
        cursor = connection.cursor()
        cursor.execute('SELECT user_id, password_hash FROM users WHERE username=?', (username,))
        user = cursor.fetchone()
        connection.close()

        # Check if username retrieved a user entry and if the password entered fits with the stored hash
        if user is not None and check_password_hash(user["password_hash"], password):
            session['user_id'] = user["user_id"]
            session.permanent = True    # won't terminate the session mantaining it on in the cache
            return redirect(url_for("home"))    # redirects to home after login
        else:
            flash('Either username or password are wrong')  # Error if the condition above isn't satisfied

    return render_template('login.html')

@app.route('/logout')
def logout():
    # terminates session
    session.pop('user_id', None)  
    return redirect(url_for("login"))

@app.route('/delete_account', methods=("POST",))
def delete():
    # check if a user is actually logged in, otherwise redirects to login
    if "user_id" not in session:
        return redirect(url_for("login"))

    # connect to db
    connection = get_db()

    # deletes all user info (thanks to cascade assessments info too) based on session's user_id
    connection.execute("DELETE FROM users WHERE user_id=?", (session["user_id"],))
    connection.commit()
    connection.close()

    return logout() # clears session and redirects to login

# Helper that returns all subjects
def get_subjects():
    connection = get_db()
    cursor = connection.cursor()

    cursor.execute("""SELECT subject_id, subject_name, level
                      FROM subjects ORDER BY subject_name""")

    subjects = cursor.fetchall()
    connection.close()

    return subjects

# Allows users to add subjects to their user_subjects
@app.route("/add_subject", methods=("POST",))
def add_subject():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    subject_id = request.form.get("subject_id", "")
    target_grade = request.form.get("target_grade", "")

    # Validation
    try:
        subject_id = int(subject_id)
        target_grade = int(target_grade)
    except ValueError:
        flash("Invalid subject or target grade")
        return redirect(url_for("home"))

    if target_grade < 1 or target_grade > 7:
        flash("Target grade must be between 1 and 7")
        return redirect(url_for("home"))

    connection = get_db()
    cursor = connection.cursor()

    # check if subject is in database
    cursor.execute("SELECT subject_id FROM subjects WHERE subject_id=?", (subject_id,))
    subject = cursor.fetchone()

    if subject is None:
        connection.close()
        flash("Invalid subject")
        return redirect(url_for("home"))

    # check if subject was already added to user_subjects
    cursor.execute("""SELECT user_subject_id FROM user_subjects 
                      WHERE user_id=? AND subject_id=?""", (session["user_id"], subject_id))

    existing_subject = cursor.fetchone()

    if existing_subject is not None:
        connection.close()
        flash("Subject already added")
        return redirect(url_for("home"))

    # adds subject to user_subjects
    cursor.execute(
        """INSERT INTO user_subjects
           (user_id, subject_id, target_grade)
           VALUES (?, ?, ?)""", (session["user_id"], subject_id, target_grade))

    connection.commit()
    connection.close()

    return redirect(url_for("home"))


# Allows users to delete subjects from their user_subjects
@app.route("/delete_subject", methods=("POST",))
def delete_subject():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    user_subject_id = request.form.get("user_subject_id", "")

    # Validation
    try:
        user_subject_id = int(user_subject_id)
    except ValueError:
        flash("Invalid subject")
        return redirect(url_for("home"))

    connection = get_db()

    # delete subject from the user_subjects 
    connection.execute("""DELETE FROM user_subjects WHERE user_id=? AND user_subject_id=?""", (session["user_id"], user_subject_id))

    connection.commit()
    connection.close()

    return redirect(url_for("home"))

# Allows users to change their target grade
@app.route("/update_target", methods=("POST",))
def update_target():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    user_subject_id = request.form.get("user_subject_id", "")
    target_grade = request.form.get("target_grade", "")

    # Validation
    try:
        user_subject_id = int(user_subject_id)
        target_grade = int(target_grade)
    except ValueError:
        flash("Invalid subject or target grade")
        return redirect(url_for("home"))

    if target_grade < 1 or target_grade > 7:
        flash("Target grade must be between 1 and 7")
        return redirect(url_for("home"))

    connection = get_db()
    cursor = connection.cursor()

    # check if the user_subjects contian the subject
    cursor.execute("""SELECT user_subject_id FROM user_subjects 
                      WHERE user_id=? AND user_subject_id=?""", (session["user_id"], user_subject_id))

    existing_subject = cursor.fetchone()

    if existing_subject is None:
        connection.close()
        flash("The user doesn't take this subject")
        return redirect(url_for("home"))

    # updates target grade
    cursor.execute(
        """UPDATE user_subjects
           SET target_grade=?
           WHERE user_id=? AND user_subject_id=?""", (target_grade, session["user_id"], user_subject_id))

    connection.commit()
    connection.close()

    return redirect(url_for("home"))

# Loads all subject specific info for user
@app.route("/subject/<int:user_subject_id>")
def load_assessments(user_subject_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db()
    cursor = connection.cursor()

    # retrieves specific subject info 
    command = """SELECT user_subjects.user_subject_id,
                        user_subjects.subject_id,
                        user_subjects.target_grade,
                        subjects.subject_name,
                        subjects.level,
                        subjects.total_topics
                FROM user_subjects JOIN subjects
                    ON user_subjects.subject_id = subjects.subject_id
                WHERE user_subjects.user_subject_id=? AND user_subjects.user_id=?"""
    
    cursor.execute(command, (user_subject_id, session["user_id"]))
    subject = cursor.fetchone() # row containing specific subject info for user

    # checks if subject exists in user_subjects
    if subject is None:
        connection.close()
        flash("Invalid subject")
        return redirect(url_for("home"))

    # retrieves assessments associated to the subject
    cursor.execute("SELECT * FROM assessments WHERE user_subject_id=? ORDER BY assessment_date", (user_subject_id,))
    assessments = cursor.fetchall()

    connection.close()

    # retrieves boundaries for subject
    boundaries = get_boundaries(subject["subject_id"], 2025, "May")

    # calculates subject stats and prediction
    analysis = analyse_subject(assessments, subject["total_topics"], boundaries)

    return render_template("subject.html", subject=subject, assessments=assessments, analysis=analysis)

# allows users to add an assessment for a subject
@app.route("/subject/<int:user_subject_id>/add_assessment",methods=("POST",))
def add_assessments(user_subject_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    assessment_type = request.form.get("assessment_type", "")
    score = request.form.get("score", "")
    maximum_score = request.form.get("maximum_score", "")
    assessment_date = request.form.get("assessment_date", "")
    topics_covered_count = request.form.get("topics_covered_count", "")

    # open db
    connection = get_db()
    cursor = connection.cursor()

    # retrieves specific subject info 
    command = """SELECT user_subjects.user_subject_id,
                        user_subjects.subject_id,
                        subjects.total_topics
                FROM user_subjects JOIN subjects
                    ON user_subjects.subject_id = subjects.subject_id
                WHERE user_subjects.user_subject_id=? AND user_subjects.user_id=?"""
    
    cursor.execute(command, (user_subject_id, session["user_id"]))
    subject = cursor.fetchone() # row containing specific subject info for user

    # checks if subject exists in user_subjects
    if subject is None:
        connection.close()
        flash("Invalid subject")
        return redirect(url_for("home"))

    # Validation
    allowed_types = [
        "Learning Experience",
        "Formative",
        "Summative",
        "Mock Exam",
        "IA"
    ]

    if assessment_type not in allowed_types:
        connection.close()
        flash("Invalid assessment type")
        return redirect(url_for("load_assessments", user_subject_id=user_subject_id))

    try:
        score = number(score)
        maximum_score = number(maximum_score)

        percentage(score, maximum_score)

        topics_covered_count = integer(topics_covered_count)

        days_between(assessment_date, assessment_date)

    except ValueError as error:
        connection.close()
        flash(str(error))
        return redirect(url_for("load_assessments", user_subject_id=user_subject_id))

    if topics_covered_count < 0 or topics_covered_count > subject["total_topics"]:
        connection.close()
        flash("Invalid number of topics covered")
        return redirect(url_for("load_assessments", user_subject_id=user_subject_id))

    # add assessment 
    command = """INSERT INTO assessments 
                    (user_subject_id, assessment_type, 
                    score, maximum_score, 
                    assessment_date, topics_covered_count) 
                VALUES (?,?,?,?,?,?)"""
    
    connection.execute(command, (user_subject_id, assessment_type, 
                                 score, maximum_score, 
                                 assessment_date, topics_covered_count))

    connection.commit()
    connection.close()
    return redirect(url_for("load_assessments", user_subject_id=user_subject_id))

# allows users to delete an assessment
@app.route("/subject/<int:user_subject_id>/delete_assessment", methods=("POST",))
def delete_assessment(user_subject_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    assessment_id = request.form.get("assessment_id", "")

    # Validation
    try:
        assessment_id = int(assessment_id)
    except ValueError:
        flash("Invalid assessment")
        return redirect(url_for("load_assessments", user_subject_id=user_subject_id))

    # open db
    connection = get_db()
    cursor = connection.cursor()

    # checks if assessment belongs to the logged in user
    command = """SELECT assessments.assessment_id
                 FROM assessments JOIN user_subjects
                    ON assessments.user_subject_id = user_subjects.user_subject_id
                 WHERE assessments.assessment_id=?
                    AND assessments.user_subject_id=?
                    AND user_subjects.user_id=?"""

    cursor.execute(command, (assessment_id, user_subject_id, session["user_id"]))

    assessment = cursor.fetchone()

    # checks if the assessment existed
    if assessment is None:
        connection.close()
        flash("Invalid assessment")
        return redirect(url_for("load_assessments", user_subject_id=user_subject_id))

    # deletes assessment
    cursor.execute("""DELETE FROM assessments
                    WHERE assessment_id=? AND user_subject_id=?""", 
                    (assessment_id, user_subject_id))

    connection.commit()
    connection.close()

    return redirect(url_for("load_assessments", user_subject_id=user_subject_id))

# helper that returns grade boundaries for a subject
def get_boundaries(subject_id, exam_year, exam_session):
    connection = get_db()
    cursor = connection.cursor()

    command = """SELECT grade, lower_boundary
                 FROM grade_boundaries
                 WHERE subject_id=? AND exam_year=? AND exam_session=?
                 ORDER BY grade"""

    cursor.execute(command, (subject_id, exam_year, exam_session))
    rows = cursor.fetchall()

    connection.close()

    boundaries = {}

    for boundary in rows:
        boundaries[boundary["grade"]] = boundary["lower_boundary"]

    return boundaries

# Calculates minimum future assessment score needed to reach target grade
@app.route("/subject/<int:user_subject_id>/advice", methods=("POST",))
def advice(user_subject_id):
    if "user_id" not in session:
        return jsonify({"error": "User not logged in"}), 401

    assessment_type = request.form.get("assessment_type", "")
    assessment_date = request.form.get("assessment_date", "")
    topics_covered_count = request.form.get("topics_covered_count", "")

    # open db
    connection = get_db()
    cursor = connection.cursor()

    # retrieves specific subject info
    command = """SELECT user_subjects.subject_id,
                        user_subjects.target_grade,
                        subjects.total_topics
                 FROM user_subjects JOIN subjects
                    ON user_subjects.subject_id = subjects.subject_id
                 WHERE user_subjects.user_subject_id=? AND user_subjects.user_id=?"""

    cursor.execute(command, (user_subject_id, session["user_id"]))
    subject = cursor.fetchone()

    # checks if subject exists
    if subject is None:
        connection.close()
        return jsonify({"error": "Invalid subject"}), 400

    # retrieves assessments associated to subject
    cursor.execute(
        """SELECT * FROM assessments
           WHERE user_subject_id=?
           ORDER BY assessment_date""", (user_subject_id,))

    assessments = cursor.fetchall()
    connection.close()

    proposed_assessment = {"assessment_type": assessment_type,
                            "assessment_date": assessment_date,
                            "topics_covered_count": topics_covered_count}

    boundaries = get_boundaries(subject["subject_id"], 2025, "May")

    # calculates advice
    try:
        required_percentage = calculate_advice(
            assessments,
            proposed_assessment,
            subject["total_topics"],
            subject["target_grade"],
            boundaries
        )

    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    return jsonify({"required_percentage": required_percentage})

if __name__ == "__main__":
    app.run(debug=True)


