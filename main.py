from flask import Flask, render_template, request, flash, redirect, abort
from flask_login import LoginManager, login_user, current_user, logout_user, login_required, current_user

from flask import request, redirect, url_for, flash
from flask_login import current_user
from flask import jsonify


import pymysql
from dynaconf import Dynaconf
import json

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
            
        elif role == "counselor":
            cursor.execute("""
                INSERT INTO CounselorProfile (UserID, CreatedAt)
                VALUES (%s, NOW())
            """, (user_id,))

        conn.commit()
        cursor.close()
        conn.close()

        flash("Account created successfully! Please log in.")
        return redirect("/login")

    return render_template("register.html.jinja")
    

@app.route("/myprofile")
@login_required
def myprofile():
    connection = connect_db()
    cursor = connection.cursor(pymysql.cursors.DictCursor)  # DictCursor is correct

    profile = None

    if current_user.role == "student":
        cursor.execute("""
            SELECT * FROM StudentProfile
            WHERE UserID = %s
        """, (current_user.id,))
        profile = cursor.fetchone()

    elif current_user.role == "counselor":
        cursor.execute("""
            SELECT * FROM CounselorProfile
            WHERE UserID = %s
        """, (current_user.id,))
        profile = cursor.fetchone()

    connection.close()

    return render_template("myprofile.html.jinja", profile=profile)


@app.route("/myprofile/edit", methods=['GET', 'POST'])
@login_required
def edit_profile():
    connection = connect_db()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    # Fetch existing profile for pre-filling form
    profile = None
    if current_user.role == "student":
        cursor.execute("SELECT * FROM StudentProfile WHERE UserID=%s", (current_user.id,))
        profile = cursor.fetchone()
    elif current_user.role == "counselor":
        cursor.execute("SELECT * FROM CounselorProfile WHERE UserID=%s", (current_user.id,))
        profile = cursor.fetchone()

    if request.method == 'POST':
        # Update User table
        name = request.form['name']
        email = request.form['email']

        cursor.execute("""
            UPDATE `User`
            SET Name=%s, Email=%s
            WHERE ID=%s
        """, (name, email, current_user.id))

        # STUDENT PROFILE
        if current_user.role == "student":
            phone = request.form.get("phone")
            address = request.form.get("address")
            bio = request.form.get("bio")

            cursor.execute("""
                UPDATE StudentProfile
                SET Phone=%s, Address=%s, Bio=%s
                WHERE UserID=%s
            """, (phone, address, bio, current_user.id))

        # COUNSELOR PROFILE
        elif current_user.role == "counselor":
            phone = request.form.get("phone")
            office = request.form.get("office")
            office_hours = request.form.get("office_hours")
            bio = request.form.get("bio")

            cursor.execute("SELECT * FROM CounselorProfile WHERE UserID=%s", (current_user.id,))
            existing = cursor.fetchone()

            if existing:
                cursor.execute("""
                    UPDATE CounselorProfile
                    SET Phone=%s, Office=%s, OfficeHours=%s, Bio=%s
                    WHERE UserID=%s
                """, (phone, office, office_hours, bio, current_user.id))
            else:
                cursor.execute("""
                    INSERT INTO CounselorProfile (UserID, Phone, Office, OfficeHours, Bio)
                    VALUES (%s, %s, %s, %s, %s)
                """, (current_user.id, phone, office, office_hours, bio))

        connection.commit()
        connection.close()
        return redirect("/myprofile")

    connection.close()
    return render_template("editmyprofile.html.jinja", profile=profile)




@app.route("/logout", methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    flash("Successfully logged out")
    return redirect ("/")

# Dashboard for students.
@app.route("/student/dashboard")
@login_required
def dashboard():
    
    connection = connect_db()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    # 1. Load counselor info
    cursor.execute("""
        SELECT User.Email, User.Name
        FROM StudentProfile
        JOIN User ON StudentProfile.CounselorUserID = User.ID
        WHERE StudentProfile.UserID = %s
    """, (current_user.id,))
    
    result = cursor.fetchone()
    counselor_email = result["Email"] if result else None
    counselor_name = result["Name"] if result else None

    # 2. Load real student profile
    cursor.execute("""
        SELECT *
        FROM StudentProfile
        WHERE UserID = %s
    """, (current_user.id,))
    student = cursor.fetchone()

    # 3. If no profile exists yet, create a default one
    if not student:
        student = {
            "Grade": "N/A",
            "GPA": "N/A",
            "Attendance": "N/A",
            "Next_Class": "N/A",
            "Next_Assignment": "N/A",
            "AllowCounselorEdit": 0
        }

    # 4. Placeholder courses
    courses = [
        {"name": "Whatever", "grade": "N/A"},
        {"name": "Whatever", "grade": "N/A"},
        {"name": "Whatever", "grade": "N/A"},
    ]

    cursor.close()
    connection.close()

    return render_template(
        "studentdashboard.html.jinja",
        student=student,
        courses=courses,
        counselor_name=counselor_name,
        counselor_email=counselor_email
    )


@app.route("/student/toggle_counselor_edit", methods=["POST"])
@login_required
def toggle_counselor_edit():
    allow_edit = 1 if request.form.get("allow_edit") == "1" else 0

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE StudentProfile
        SET AllowCounselorEdit = %s
        WHERE UserID = %s
    """, (allow_edit, current_user.id))

    conn.commit()
    cur.close()
    conn.close()

    return redirect("/student/dashboard")



@app.route("/student/recommendation")
@login_required
def recommendations():

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT ID, Name, Email
        FROM User
        WHERE Role = %s """ , (current_user.id))

    counselors = cursor.fetchall()
    connection.close()

    return render_template( "recommendation.html.jinja", counselors=counselors
    )


@app.route("/student/recommendation/addcounselor")
@login_required
def add_counselor():

    connection = connect_db()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    cursor.execute("SELECT ID, Name, Email FROM User WHERE Role='counselor'")

    counselors = cursor.fetchall()
    connection.close()

    return render_template(
        "addcounselor.html.jinja",
        counselors=counselors,
    )

@app.route("/student/recommendation/addcounselor/processing", methods=["POST"])
@login_required
def add_counselor_form():
    counselor_id = request.form["counselor_id"] 
    grade = request.form["grade"]
    comments = request.form.get("comments")  

    connection = connect_db()
    cursor = connection.cursor()

    # Assign counselor to student
    cursor.execute("""
        UPDATE StudentProfile
        SET CounselorUserID = %s
        WHERE UserID = %s
    """, (counselor_id, current_user.id))

    # 2. NEW: Insert into CounselorStudent (this is what makes the counselor see the student)
    cursor.execute("""
        INSERT INTO CounselorStudent (CounselorUserID, StudentUserID)
        VALUES (%s, %s)
    """, (counselor_id, current_user.id))


    # Save recommendation request using INSERT ... SELECT
    cursor.execute("""
        INSERT INTO StudentProfile (Grade, Comments, UserID , CounselorUserID)
        SELECT %s, %s, %s, %s
    """, (grade, comments, current_user.id, counselor_id))

    connection.commit()
    connection.close()

    return redirect("/student/dashboard")

@app.route("/student/recommendation/update", methods=["POST"])
@login_required
def update_recommendation():

    counselor_id = request.form["counselor_id"]
    grade = request.form["grade"]
    comments = request.form.get("comments")

    connection = connect_db()
    cursor = connection.cursor()

    # Update student profile counselor
    cursor.execute("""
        UPDATE StudentProfile
        SET CounselorUserID = %s
        WHERE UserID = %s
    """, (counselor_id, current_user.id))

    # Update StudentProfile
    cursor.execute("""
    UPDATE StudentProfile (Grade, Comments, UserID , CounselorUserID)
    VALUES (%s, %s, %s, %s)
""", (counselor_id, grade, comments, current_user.id))

    connection.commit()
    connection.close()

    return redirect("/student/dashboard")

@app.route("/student/recommendation/review")
@login_required
def review_recommendation():
    connection = connect_db()
    cursor = connection.cursor()
    cursor.execute("""
    SELECT * FROM `Application`
    JOIN `User` ON `Application`.`UserID` = `User`.`ID`
    WHERE StudentUserID = %s
    """, (current_user.id,))
    information = cursor.fetchall()
    connection.close()
    return render_template("review.html.jinja" , information=information)

#dashboard for counselors.
@app.route("/counselor/dashboard")
@login_required
def counselor_dashboard():
    if current_user.role != "counselor":
        abort(404)
    
    connection = connect_db()

    cursor = connection.cursor(pymysql.cursors.DictCursor)

    cursor.execute("""
    SELECT * FROM `StudentProfile`
    JOIN `User` ON `StudentProfile`.`UserID` = `User`.`ID`
    WHERE CounselorUserID = %s
    """, (current_user.id,))

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

    cursor = connection.cursor(pymysql.cursors.DictCursor)

    cursor.execute("""
    SELECT * FROM `StudentProfile`
    JOIN `User` ON `StudentProfile`.`UserID` = `User`.`ID`
    WHERE CounselorUserID = %s
    """, (current_user.id,))

    result = cursor.fetchall()

    connection.close()
    return render_template("counselorrecommendation.html.jinja", user=result)




@app.route("/student/academic_record")
@login_required
def student_academic_record():
    conn = connect_db()
    cur = conn.cursor()

    # find student profile
    cur.execute("SELECT ID FROM StudentProfile WHERE UserID = %s", (current_user.id,))
    profile = cur.fetchone()

    transcript_data = None

    if profile:
        student_profile_id = profile["ID"]

        # latest transcript
        cur.execute("""
            SELECT * FROM Transcript 
            WHERE StudentID = %s 
            ORDER BY CreatedAt DESC LIMIT 1
        """, (student_profile_id,))
        transcript = cur.fetchone()

        if transcript:
            transcript_id = transcript["ID"]

            # load grades
            cur.execute("SELECT * FROM Grade WHERE TranscriptID = %s", (transcript_id,))
            grades = cur.fetchall()

            grade_list = []

            for g in grades:
                grade_id = g["ID"]
                grade_level = g["GradeLevel"]

                # load subjects
                cur.execute("SELECT * FROM Subject WHERE GradeID = %s", (grade_id,))
                subjects = cur.fetchall()

                subject_list = []
                for s in subjects:
                    subject_list.append({
                        "Name": s["SubjectName"] or "",
                        "Letter": s["FinalGrade"] or "",
                        "Credits": float(s["Credits"]) if s["Credits"] is not None else 0,
                        "Marks": s["Marks"] if s["Marks"] is not None else None,
                        "Preference": s["Preference"] if s["Preference"] is not None else None
                    })



                grade_list.append({
                    "GradeLevel": grade_level,
                    "Subjects": subject_list
                })

            transcript_data = {
                "GPA": float(transcript["GPA"]) if transcript["GPA"] is not None else None,
                "Grades": grade_list
            }

    cur.close()
    conn.close()

    return render_template(
        "student_academic_record.html.jinja",
        transcript_json=json.dumps(transcript_data) if transcript_data else "null"
    )


#users transcript is saved in database.
@app.route("/save_transcript", methods=["POST"])
@login_required
def save_transcript():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"status": "error", "message": "No data received"}), 400

        conn = connect_db()
        cur = conn.cursor()

        # find StudentProfile
        cur.execute("SELECT ID FROM StudentProfile WHERE UserID = %s", (current_user.id,))
        profile = cur.fetchone()

        if not profile:
            cur.close()
            conn.close()
            return jsonify({"status": "error", "message": "Student profile not found"}), 400

        student_profile_id = profile["ID"]

        overall_gpa = data.get("GPA", None)
        grades_data = data.get("Grades", [])

        # insert transcript
        cur.execute(
            "INSERT INTO Transcript (StudentID, CourseID, GPA, CreatedAt) "
            "VALUES (%s, NULL, %s, NOW())",
            (student_profile_id, overall_gpa)
        )
        transcript_id = cur.lastrowid

        # insert grades + subjects
        for grade in grades_data:
            grade_level = grade.get("GradeLevel")

            cur.execute(
                "INSERT INTO Grade (TranscriptID, GradeLevel) VALUES (%s, %s)",
                (transcript_id, grade_level)
            )
            grade_id = cur.lastrowid

            for subject in grade.get("Subjects", []):
                name = subject.get("Name")
                letter = subject.get("Letter")
                credits = subject.get("Credits")
                marks = subject.get("Marks")
                preference = subject.get("Preference")


                cur.execute(
                    "INSERT INTO Subject (GradeID, SubjectName, FinalGrade, Credits, Marks, Preference) "
                    "VALUES (%s, %s, %s, %s, %s, %s)",
                    (grade_id, name, letter, credits, marks, preference)
                )

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"status": "success", "message": "Transcript saved successfully."})

    except Exception as e:
        print("FULL ERROR:", repr(e))
        return jsonify({"status": "error", "message": "Server error: " + repr(e)}), 500


@app.route("/counselor/recommendation/addapplication/<user_id>")
@login_required
def add_application(user_id):

    connection = connect_db()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    cursor.execute("""
    SELECT * FROM `StudentProfile`
    JOIN `User` ON `StudentProfile`.`UserID` = `User`.`ID`
    WHERE User.ID = %s
    """ , (user_id,))

    result = cursor.fetchone()
    connection.close()
    
    return render_template(
        "addapplication.html.jinja",
        user=result
    )

@app.route("/counselor/recommendation/addapplication/<user_id>/adding", methods=['POST'])
@login_required
def adding_app(user_id):
    Major = request.form["Major"]
    Comments = request.form["Comments"]
    student_id = request.form["student_id"]

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("""
    SELECT * FROM `StudentProfile`
    JOIN `User` ON `StudentProfile`.`UserID` = `User`.`ID`
    WHERE User.ID = %s
    """ , (user_id,))
    users = cursor.fetchone()
    
    cursor.execute("""
        INSERT INTO `Application`
        (UserID, Major, Comments, StudentUserID)
        VALUES (%s, %s, %s, %s)
    """, (current_user.id, Major, Comments, student_id,))

    connection.commit()
    connection.close()

    return redirect("/counselor/dashboard")





#List students for counselor + render page
@app.route("/counselor/academic_record")
@login_required
def counselor_academic_records():
    # Ensure this user is a counselor
    if current_user.role != "counselor":
        abort(403)

    conn = connect_db()
    cur = conn.cursor()

    # Get all students assigned to this counselor
    cur.execute("""
        SELECT 
            cs.StudentUserID AS StudentUserID,
            u.Name AS StudentName,
            u.Email AS StudentEmail,
            sp.Grade AS Grade,
            sp.StudentType AS StudentType,
            sp.AllowCounselorEdit AS AllowEdit
        FROM CounselorStudent cs
        JOIN User u ON cs.StudentUserID = u.ID
        JOIN StudentProfile sp ON sp.UserID = u.ID
        WHERE cs.CounselorUserID = %s
        ORDER BY u.Name
    """, (current_user.id,))
    students = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "counselor_academic_record.html.jinja",
        students=students
    )





#Fetch a specific student’s transcript (JSON)
@app.route("/counselor/student_transcript/<int:student_user_id>")
@login_required
def counselor_student_transcript(student_user_id):
    if current_user.role != "counselor":
        abort(403)

    conn = connect_db()
    cur = conn.cursor()

    # Ensure this student belongs to this counselor
    cur.execute("""
        SELECT 1
        FROM CounselorStudent
        WHERE CounselorUserID = %s AND StudentUserID = %s
    """, (current_user.id, student_user_id))
    link = cur.fetchone()
    if not link:
        cur.close()
        conn.close()
        abort(403)

    # Get student profile
    cur.execute("""
        SELECT ID, Grade, StudentType, AllowCounselorEdit
        FROM StudentProfile
        WHERE UserID = %s
    """, (student_user_id,))
    profile = cur.fetchone()
    if not profile:
        cur.close()
        conn.close()
        return jsonify({"error": "Student profile not found"}), 404

    student_profile_id = profile["ID"]

    # Latest transcript
    cur.execute("""
        SELECT * FROM Transcript
        WHERE StudentID = %s
        ORDER BY CreatedAt DESC LIMIT 1
    """, (student_profile_id,))
    transcript = cur.fetchone()

    transcript_data = None
    if transcript:
        transcript_id = transcript["ID"]

        cur.execute("SELECT * FROM Grade WHERE TranscriptID = %s", (transcript_id,))
        grades = cur.fetchall()

        grade_list = []
        for g in grades:
            grade_id = g["ID"]
            grade_level = g["GradeLevel"]

            cur.execute("SELECT * FROM Subject WHERE GradeID = %s", (grade_id,))
            subjects = cur.fetchall()

            subject_list = []
            for s in subjects:
                subject_list.append({
                    "Name": s["SubjectName"] or "",
                    "Letter": s["FinalGrade"] or "",
                    "Credits": float(s["Credits"]) if s["Credits"] is not None else 0,
                    "Marks": s["Marks"] if s["Marks"] is not None else None,
                    "Preference": s["Preference"] if s["Preference"] is not None else None
                })

            grade_list.append({
                "GradeLevel": grade_level,
                "Subjects": subject_list
            })

        transcript_data = {
            "GPA": float(transcript["GPA"]) if transcript["GPA"] is not None else None,
            "Grades": grade_list
        }

    cur.close()
    conn.close()

    return jsonify({
        "profile": {
            "Grade": profile["Grade"],
            "StudentType": profile["StudentType"],
            "AllowCounselorEdit": bool(profile["AllowCounselorEdit"])
        },
        "transcript": transcript_data
    })




#Counselor saves transcript edits (if allowed)
@app.route("/counselor/save_transcript/<int:student_user_id>", methods=["POST"])
@login_required
def counselor_save_transcript(student_user_id):
    if current_user.role != "counselor":
        abort(403)

    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No data received"}), 400

    conn = connect_db()
    cur = conn.cursor()

    # Ensure relationship + get profile
    cur.execute("""
        SELECT sp.ID, sp.AllowCounselorEdit, sp.Grade
        FROM CounselorStudent cs
        JOIN StudentProfile sp ON sp.UserID = cs.StudentUserID
        WHERE cs.CounselorUserID = %s AND cs.StudentUserID = %s
    """, (current_user.id, student_user_id))
    row = cur.fetchone()
    if not row:
        cur.close()
        conn.close()
        abort(403)

    if not row["AllowCounselorEdit"]:
        cur.close()
        conn.close()
        return jsonify({"status": "error", "message": "Student has not allowed counselor editing."}), 403

    student_profile_id = row["ID"]
    current_profile_grade = row["Grade"]

    overall_gpa = data.get("GPA", None)
    grades_data = data.get("Grades", [])

    # Insert new transcript (same pattern as student)
    cur.execute(
        "INSERT INTO Transcript (StudentID, CourseID, GPA, CreatedAt) "
        "VALUES (%s, NULL, %s, NOW())",
        (student_profile_id, overall_gpa)
    )
    transcript_id = cur.lastrowid

    max_grade_level = current_profile_grade

    for grade in grades_data:
        grade_level = grade.get("GradeLevel")
        if grade_level and (max_grade_level is None or grade_level > max_grade_level):
            max_grade_level = grade_level

        cur.execute(
            "INSERT INTO Grade (TranscriptID, GradeLevel) VALUES (%s, %s)",
            (transcript_id, grade_level)
        )
        grade_id = cur.lastrowid

        for subject in grade.get("Subjects", []):
            cur.execute(
                "INSERT INTO Subject (GradeID, SubjectName, FinalGrade, Credits, Marks, Preference) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (
                    grade_id,
                    subject.get("Name"),
                    subject.get("Letter"),
                    subject.get("Credits"),
                    subject.get("Marks"),
                    subject.get("Preference"),
                )
            )

    # Optionally sync grade
    cur.execute("""
        UPDATE StudentProfile
        SET Grade = %s
        WHERE ID = %s
    """, (max_grade_level, student_profile_id))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"status": "success", "message": "Transcript updated by counselor."})

