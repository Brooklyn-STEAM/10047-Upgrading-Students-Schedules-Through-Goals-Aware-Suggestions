from flask import Flask, render_template, request, flash, redirect, abort
from flask_login import LoginManager, login_user, current_user, logout_user, login_required, current_user

import pymysql
from flask_login import LoginManager, login_user , logout_user, login_required, current_user
from dynaconf import Dynaconf

app = Flask(__name__)

config = Dynaconf(settings_file = ["settings.toml"])

app.secret_key = config.secret_key

login_manager = LoginManager(app) 

login_manager.login_view = "/login"

class User:
    is_authenticated = True
    is_active = True
    is_anonymous = False

    def __init__(self, result):
        self.name = result['Name']
        self.email = result['Email']
        self.id = result['ID']
        self.role = result['Role']
        

    def get_id(self):
        return str(self.id)

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html.jinja'), 404 

@login_manager.user_loader
def load_user(user_id):
    connection = connect_db()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM `User` WHERE `ID` = %s", (user_id))
    result = cursor.fetchone()
    connection.close()

    if result is None:
        return None
    return User(result)


def connect_db():
    conn = pymysql.connect(
        host="db.steamcenter.tech",
        user=config.username,     # <-- changed from 'username' to 'user'
        password=config.password,
        database="course_track",
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor
    )
    return conn


@app.route("/")
def index():
    return render_template("homepage.html.jinja")



@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        connection = connect_db()
        cursor = connection.cursor()

        cursor.execute(
            "SELECT * FROM `User` WHERE `Email` = %s",
            (email,)
        )

        result = cursor.fetchone()

        connection.close()

        if result is None:
            flash("No user found")
        elif password != result['Password']:  # plain-text check
            flash("Incorrect password")
        else:
            login_user(User(result))  # Your user class
            if current_user.role == "student":
                return redirect("/sdashboard")
            elif current_user.role == "counselor":
                return redirect("/cdashboard")
            else:
                return redirect("/")


    return render_template("/login.html.jinja")



@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']  # 'student' or 'counselor'


        connection = connect_db()
        cursor = connection.cursor()


        # Check if user already exists
        cursor.execute("SELECT * FROM `User` WHERE `Email` = %s", (email,))
        existing_user = cursor.fetchone()


        if existing_user:
            flash("Email already registered")
            cursor.close()
            connection.close()
            return redirect("/signup")


        # Insert new user
        cursor.execute(
            "INSERT INTO `User` (Name, Email, Password, Role) VALUES (%s, %s, %s, %s)",
            (name, email, password, role)
        )
        connection.commit()


        # Get the new user's ID
        user_id = cursor.lastrowid
        cursor.close()
        connection.close()


        # Optional: create a StudentProfile if role is student
        if role == 'student':
            connection = connect_db()
            cursor = connection.cursor()
            cursor.execute(
                "INSERT INTO `StudentProfile` (UserID, Name) VALUES (%s, %s)",
                (user_id, name)
            )
            connection.commit()
            cursor.close()
            connection.close()


        flash("Account created successfully! Please log in.")
        return redirect("/login")


    return render_template("register.html.jinja")


@app.route("/logout", methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    flash("Successfully logged out")
    return redirect ("/")

#Dashboard for students.
@app.route("/student/dashboard")
@login_required
def student_dashboard():
    if current_user.role != "student":
        return redirect("/theerror")

    return render_template("studentdashboard.html.jinja")

#dashboard for counselors.
@app.route("/counselor/dashboard")
@login_required
def counselor_dashboard():
    if current_user.role != "counselor":
        return redirect("/theerror")
    
    connection = connect_db()

    cursor = connection.cursor()

    cursor.execute("SELECT * FROM `User` ")

    result = cursor.fetchall()

    connection.close()

    return render_template("counselor_dashboard.html.jinja", user=result)









#404 error page
@app.route("/theerror")
def not_found():
    return render_template("404.html.jinja")

@app.route("/student/recommendation")
def recommendations():
    return render_template("recommendation.html.jinja")

@app.route("/counselor/recommendation")
def counselor_recommendations():
    return render_template("counselorrecommendation.html.jinja")

@app.route('/student/academic_record', methods=['GET', 'POST'])
@login_required
def student_academicrecord():
    if request.method == "POST":
        print(request.form)
        return redirect("/student/academic_record")

    return render_template("student_academic_record.html.jinja")

