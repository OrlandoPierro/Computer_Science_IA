from flask import Flask, render_template, redirect, request, session, flash, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from secrets import token_hex
import sqlite3 

from database import get_db

app = Flask(__name__)
app.permanent_session_lifetime = 604800
app.secret_key = token_hex(32)


@app.route("/")
def home():
    user_id = session.get('user_id')

    if not user_id:
        return redirect(url_for("login"))
    
    connection = get_db()
    cursor = connection.cursor()

    cursor.execute('SELECT username FROM users WHERE user_id=?', (user_id,))
    user = cursor.fetchone()

    if user is None:
        connection.close()
        return logout()

    command = """SELECT user_subjects.user_subject_id, 
                        subjects.subject_name, 
                        subjects.level, 
                        subjects.total_topics, 
                        user_subjects.target_grade 
                FROM user_subjects JOIN subjects 
                        ON user_subjects.subject_id=subjects.subject_id 
                WHERE user_subjects.user_id=?"""
    
    cursor.execute(command, (user_id,))
    user_subjects = cursor.fetchall()  

    connection.close()

    return render_template('index.html', username=user["username"], user_subjects=user_subjects)

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


if __name__ == "__main__":
    app.run(debug=True)