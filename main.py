from flask import Flask, render_template, request, flash, redirect, abort
from flask_login import LoginManager, login_user, current_user, logout_user, login_required, current_user

from flask import request, redirect, url_for, flash
from flask_login import current_user
from flask import jsonify


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
                return redirect("/student/dashboard")
            elif current_user.role == "counselor":
                return redirect("/counselor/dashboard")
            else:
                return redirect("/")


    return render_template("/login.html.jinja")



@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        conn = connect_db()
        cursor = conn.cursor()

        # check duplicate
        cursor.execute("SELECT * FROM User WHERE Email=%s", (email,))
        if cursor.fetchone():
            flash("Email already registered")
            cursor.close()
            conn.close()
            return redirect("/login")

        # insert user
        cursor.execute(
            "INSERT INTO User (Name, Email, Password, Role) VALUES (%s,%s,%s,%s)",
            (name, email, password, role)
        )
        user_id = cursor.lastrowid

        # insert student profile
        if role == "student":
            student_type = request.form['student_type']
            grade_val = 12 if student_type == "Graduate" else int(request.form['grade'])

            cursor.execute("""
                INSERT INTO StudentProfile (UserID, Grade, StudentType, CreatedAt)
                VALUES (%s, %s, %s, NOW())
            """, (user_id, grade_val, student_type))

        conn.commit()
        cursor.close()
        conn.close()

        flash("Account created successfully! Please log in.")
        return redirect("/login")

    return render_template("register.html.jinja")
    

@app.route("/myprofile")
@login_required
def my_profile():
    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM `User` WHERE `ID` = %s", (current_user.id))
    result = cursor.fetchone()

    connection.close()

    return render_template("myprofile.html.jinja", user=result)




@app.route("/logout", methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    flash("Successfully logged out")
    return redirect ("/")

#Dashboard for students.
@app.route("/student/dashboard")
def dashboard():
    student = {
        "grade": "N/A",
        "gpa": "N/A",
        "attendance":"N/A",
        "next_class": "N/A",
        "next_assignment": "N/A"
    }

    courses = [
        {"name": "Whatever", "grade": "N/A"},
        {"name": "Whatever", "grade": "N/A"},
        {"name": "Whatever", "grade": "N/A"},
    ]

    return render_template("studentdashboard.html.jinja", student=student, courses=courses)


@app.route("/student/recommendation")
def recommendations():
    return render_template("recommendation.html.jinja")

@app.route("/student/recommendation/addcounselor")
def add_counselor():
    return render_template("addcounselor.html.jinja")

@app.route("/student/recommendation/addcounselor/processing", methods=['POST'])
@login_required
def add_counselor_form():
    FirstName = request.form["firstname"]
    LastName = request.form["lastname"]
    Email = request.form["emailaddress"]
    Grade = request.form["grade"]
    Comments = request.form["comments"]

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO `Recommendation`
        (`FirstName`, `LastName`, `Email`, `Grade`, `Comments`, `UserID`)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (FirstName, LastName, Email, Grade, Comments, current_user.id))

    connection.commit()
    connection.close()

    return redirect("/student/dashboard")

#dashboard for counselors.
@app.route("/counselor/dashboard")
@login_required
def counselor_dashboard():
    if current_user.role != "counselor":
        abort(404)
    
    connection = connect_db()

    cursor = connection.cursor()

    cursor.execute("SELECT * FROM `User` ")

    result = cursor.fetchall()

    connection.close()

    return render_template("counselor_dashboard.html.jinja", user=result)




@app.route("/counselor/dashboard/<student_id>")
def student_profile(student_id):
   connection = connect_db()

   cursor = connection.cursor()

   cursor.execute("""

    SELECT * FROM `User`
    
    WHERE `ID` = %s
   """, (student_id))
   result = cursor.fetchone()
   connection.close()
   return render_template("studentprofile.html.jinja", students=student_id , student=result)

@app.route("/counselor/recommendation")
@login_required
def counselor_recommendations():
    if current_user.role != "counselor":
        abort(404)
    
    connection = connect_db()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT * FROM `Recommendation`
        
    """)

    result = cursor.fetchall()

    connection.close()
    return render_template("counselorrecommendation.html.jinja", user=result)





@app.route('/student/academic_record', methods=['GET', 'POST'])
@login_required
def student_academicrecord():
    if request.method == "POST":
        print(request.form)
        return redirect("/student/academic_record")

    return render_template("student_academic_record.html.jinja")

@app.route("/counselor/recommendation/addapplication/<applicant_id>")
@login_required
def add_application(applicant_id):
    connection = connect_db()
    cursor = connection.cursor()
    cursor.execute("""
        SELECT * FROM `Recommendation`
        WHERE `ID` = %s
    """, (applicant_id))
    result = cursor.fetchone()
    connection.close()
    return render_template("addapplication.html.jinja" , applicant=result)

@app.route("/counselor/recommendation/addapplication/adding", methods=['POST'])
@login_required
def adding_app():
    Major = request.form["Major"]
    Application_type = request.form["Type"]
    Comments = request.form["Comments"]

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO Application
        (UserID, Major, Graduate, Comments)
        VALUES (%s, %s, %s, %s)
    """, (current_user.id, Major, Application_type, Comments))

    connection.commit()
    connection.close()

    return redirect("/counselor/dashboard")


#404 error page
@app.errorhandler(404)
def not_found(error):
    return render_template("404.html.jinja"), 404

