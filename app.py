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
    return render_template("index.html")

@app.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        # access the submitted values
        username = request.form.get('username').strip()
        password = request.form.get('password')

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
        username = request.form['username']
        password = request.form['password']
        password = hashlib.sha256(password.encode('utf-8')).hexdigest()
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        cursor.execute('SELECT id FROM users WHERE username=? AND password=?', (username, password))
        user = cursor.fetchone()
        connection.close()
        if user is not None:
            session['user_id'] = user[0]
            session.permanent = True 
            return redirect('/')
        else:
            flash('Username o password errati')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect('/')


if __name__ == "__main__":
    app.run(debug=True)