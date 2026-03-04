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
        role = request.form['role']

        conn = connect_db()
        cursor = conn.cursor()

        # check duplicate
        cursor.execute("SELECT * FROM `User` WHERE `Email`=%s", (email,))
        if cursor.fetchone():
            flash("Email already registered")
            cursor.close()
            conn.close()
            return redirect("/signup")

        # insert user
        cursor.execute("INSERT INTO `User` (Name, Email, Password, Role) VALUES (%s,%s,%s,%s)", (name,email,password,role))
        user_id = cursor.lastrowid

        if role == "student":
            student_type = request.form['student_type']
            grade_val = 12 if student_type=="Graduate" else int(request.form['grade'])
            cursor.execute("INSERT INTO `StudentProfile` (UserID, Grade, StudentType, CreatedAt) VALUES (%s,%s,%s,NOW())",
                           (user_id, grade_val, student_type))
            conn.commit()

        cursor.close()
        conn.close()
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
    if current_user.role != "student":
        return redirect("/theerror")
    return render_template("recommendation.html.jinja")

@app.route("/counselor/recommendation")
def counselor_recommendations():
    if current_user.role != "counselor":
        return redirect("/theerror")
    return render_template("counselorrecommendation.html.jinja")





@app.route('/student/academic_record', methods=['GET', 'POST'])
@login_required
def student_academicrecord():
    if request.method == "POST":
        print(request.form)
        return redirect("/student/academic_record")

    return render_template("student_academic_record.html.jinja")



# the student transcript is saved into the database.
@app.route("/save_transcript", methods=["POST"])
@login_required
def save_transcript():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"status": "error", "message": "No data received"}), 400

        # ✅ CONNECT TO DATABASE FIRST
        conn = connect_db()
        cursor = conn.cursor()

        # ✅ Get StudentProfile ID for logged-in user
        cursor.execute(
            "SELECT ID FROM StudentProfile WHERE UserID = %s",
            (current_user.id,)
        )

        result = cursor.fetchone()

        if not result:
            cursor.close()
            conn.close()
            return jsonify({"status": "error", "message": "Student profile not found"}), 400

        student_profile_id = result[0]

        transcript_gpa = data.get("GPA", None)
        grades_data = data.get("Grades", [])

        # 1️⃣ Insert Transcript
        cursor.execute(
            "INSERT INTO Transcript (StudentID, GPA) VALUES (%s, %s)",
            (student_profile_id, transcript_gpa)
        )
        transcript_id = cursor.lastrowid

        # 2️⃣ Insert Grades
        for grade in grades_data:
            grade_level = grade.get("GradeLevel")
            grade_gpa = grade.get("GPA", None)

            cursor.execute(
                "INSERT INTO Grade (TranscriptID, GradeLevel, GPA) VALUES (%s, %s, %s)",
                (transcript_id, grade_level, grade_gpa)
            )
            grade_id = cursor.lastrowid

            # 3️⃣ Insert Subjects
            for subject in grade.get("Subjects", []):
                subject_name = subject.get("Name")
                marks = subject.get("Marks")
                letter = subject.get("Letter")
                credits = subject.get("Credits")

                cursor.execute(
                    """
                    INSERT INTO Subject 
                    (GradeID, SubjectName, FinalGrade, Marks, Credits)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (grade_id, subject_name, letter, marks, credits)
                )

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "status": "success",
            "message": "Transcript saved successfully."
        })

    except Exception as e:
        print("FULL ERROR:", repr(e))
    return jsonify({
        "status": "error",
        "message": repr(e)
    }), 500




