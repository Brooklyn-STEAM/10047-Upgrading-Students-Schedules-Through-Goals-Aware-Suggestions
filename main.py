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

def calculate_gpa_for_transcript(grades, gpa_settings):
    # Extract settings safely
    system = gpa_settings.get("System", "us_4")
    max_gpa = float(gpa_settings.get("MaxGPA", 4.0))

    # Validate ScaleJSON
    scale = gpa_settings.get("ScaleJSON", {})
    if not isinstance(scale, dict) or "bands" not in scale:
        scale = {"bands": []}

    bands = scale.get("bands", [])
    if not isinstance(bands, list):
        bands = []

    # Validate WeightingJSON
    weighting = gpa_settings.get("WeightingJSON", {})
    if not isinstance(weighting, dict):
        weighting = {}

    def marks_to_letter_and_points(marks):
        if marks is None:
            return None, None

        percent = float(marks)

        # Try custom bands first
        for band in bands:
            try:
                band_min = float(band.get("min", 0))
                band_max = float(band.get("max", 100))
                if band_min <= percent <= band_max:
                    letter = band.get("letter")
                    points = float(band.get("points", 0.0))
                    return letter, min(points, max_gpa)
            except:
                continue  # skip malformed band

        # Fallback US scale
        if percent >= 90:
            return "A", min(4.0, max_gpa)
        elif percent >= 80:
            return "B", min(3.0, max_gpa)
        elif percent >= 70:
            return "C", min(2.0, max_gpa)
        elif percent >= 60:
            return "D", min(1.0, max_gpa)
        else:
            return "F", 0.0

    overall_quality_points = 0.0
    overall_credits = 0.0

    for grade in grades:
        grade_quality_points = 0.0
        grade_credits = 0.0

        for subj in grade["Subjects"]:
            credits = subj.get("Credits") or 0
            marks = subj.get("Marks")
            category = subj.get("MainCategory")

            if credits and marks is not None:
                letter, base_points = marks_to_letter_and_points(marks)

                # Apply weighting
                weight = float(weighting.get(category, 1.0))
                points = min(base_points * weight, max_gpa)

                subj["Letter"] = letter
                subj["Points"] = points

                grade_quality_points += points * float(credits)
                grade_credits += float(credits)
            else:
                subj["Letter"] = None
                subj["Points"] = None

        if grade_credits > 0:
            grade["GPA"] = round(grade_quality_points / grade_credits, 2)
            overall_quality_points += grade_quality_points
            overall_credits += grade_credits
        else:
            grade["GPA"] = None

    overall_gpa = round(overall_quality_points / overall_credits, 2) if overall_credits > 0 else None
    return overall_gpa, grades



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
        WHERE Role = 'counselor' """)

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

    cursor.execute("""
        SELECT * FROM Recommendation
        WHERE UserID = %s
    """, (current_user.id,))
    recommendation = cursor.fetchone()

    connection.close()

    return render_template(
        "addcounselor.html.jinja",
        counselors=counselors,
        recommendation=recommendation
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
        INSERT INTO Recommendation (Email, Grade, Comments, UserID)
        SELECT Email, %s, %s, %s
        FROM User
        WHERE ID = %s
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

    # Update recommendation
    cursor.execute("""
    UPDATE Recommendation r
    JOIN User u ON u.ID = %s
    SET r.Email = u.Email,
        r.Grade = %s,
        r.Comments = %s
    WHERE r.UserID = %s
""", (counselor_id, grade, comments, current_user.id))

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

    cursor = connection.cursor(pymysql.cursors.DictCursor)

    cursor.execute("SELECT * FROM `StudentProfile` Join `User` ON `StudentProfile`.`UserID` = `User`.`ID` WHERE CounselorUserID = %s", (current_user.id,))

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

    cursor.execute("SELECT * FROM `StudentProfile` Join `User` ON `StudentProfile`.`UserID` = `User`.`ID` WHERE CounselorUserID = %s", (current_user.id,))

    result = cursor.fetchall()

    connection.close()
    return render_template("counselorrecommendation.html.jinja", user=result)






@app.route("/student/academic_record")
@login_required
def student_academic_record():
    if current_user.role != "student":
        abort(403)

    conn = connect_db()
    cur = conn.cursor()

    # find student profile
    cur.execute("SELECT ID FROM StudentProfile WHERE UserID = %s", (current_user.id,))
    profile = cur.fetchone()

    # If no student profile exists → return empty transcript
    if not profile:
        cur.close()
        conn.close()
        return render_template(
            "student_academic_record.html.jinja",
            transcript_json="null"
        )

    transcript_data = None
    student_profile_id = profile["ID"]

    # latest transcript
    cur.execute("""
        SELECT * FROM Transcript 
        WHERE StudentID = %s 
        ORDER BY CreatedAt DESC LIMIT 1
    """, (student_profile_id,))
    transcript = cur.fetchone()

    # If no transcript exists → return empty transcript JSON
    if not transcript:
        cur.close()
        conn.close()
        return render_template(
            "student_academic_record.html.jinja",
            transcript_json="null"
        )

    # Ownership check AFTER confirming transcript exists
    if transcript["StudentID"] != student_profile_id:
        cur.close()
        conn.close()
        abort(403)

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
                "Credits": float(s["Credits"]) if s["Credits"] is not None else None,
                "Marks": float(s["Marks"]) if s["Marks"] is not None else None,
                "Preference": s["Preference"] if s["Preference"] is not None else None,
                "MainCategory": s.get("MainCategory") if "MainCategory" in s else None,
                "CourseName": s.get("CourseName") if "CourseName" in s else None,
                "CustomCourseName": s.get("CustomCourseName") if "CustomCourseName" in s else None
            })

        grade_list.append({
            "GradeLevel": grade_level,
            "Subjects": subject_list
        })

    # load GPA settings for this user
    cur.execute("""
        SELECT * FROM GPA_Settings
        WHERE UserID = %s
        ORDER BY UpdatedAt DESC
        LIMIT 1
    """, (current_user.id,))
    settings = cur.fetchone()

    if settings:
        gpa_settings = {
            "System": settings["System"],
            "MaxGPA": float(settings["MaxGPA"]) if settings["MaxGPA"] is not None else 4.0,
            "ScaleJSON": json.loads(settings["ScaleJSON"]) if settings["ScaleJSON"] else {},
            "WeightingJSON": json.loads(settings["WeightingJSON"]) if settings["WeightingJSON"] else {}
        }
    else:
        gpa_settings = {
            "System": "us_4",
            "MaxGPA": 4.0,
            "ScaleJSON": {},
            "WeightingJSON": {}
        }

    # calculate GPA using backend logic
    overall_gpa, grade_list = calculate_gpa_for_transcript(grade_list, gpa_settings)

    transcript_data = {
        "GPA": overall_gpa,
        "Grades": grade_list,
        "GPASettings": gpa_settings
    }

    cur.close()
    conn.close()

    return render_template(
        "student_academic_record.html.jinja",
        transcript_json=json.dumps(transcript_data)
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

        grades_data = data.get("Grades", [])

        # Insert transcript (no GPA column anymore)
        cur.execute(
            "INSERT INTO Transcript (StudentID, CourseID, CreatedAt) VALUES (%s, NULL, NOW())",
            (student_profile_id,)
        )
        transcript_id = cur.lastrowid

        # Insert grades + subjects
        for grade in grades_data:
            grade_level = grade.get("GradeLevel")


            if not isinstance(grade_level, int) or grade_level < 1 or grade_level > 12:
                return jsonify({"status": "error", "message": "Invalid grade level"}), 400
        
            # Insert grade (no GPA column anymore)
            cur.execute(
                "INSERT INTO Grade (TranscriptID, GradeLevel) VALUES (%s, %s)",
                (transcript_id, grade_level)
            )
            grade_id = cur.lastrowid

            for subject in grade.get("Subjects", []):
                name = subject.get("Name")
                credits = subject.get("Credits")
                marks = subject.get("Marks")
                preference = subject.get("Preference")

                main_category = subject.get("MainCategory")
                course_name = subject.get("CourseName")
                custom_course_name = subject.get("CustomCourseName")

                # If CourseName == "Other", ensure CustomCourseName exists
                if course_name == "Other" and not custom_course_name:
                    custom_course_name = name  # fallback


                if not name or len(name) > 100:
                    return jsonify({"status": "error", "message": "Invalid subject name"}), 400

                # Insert subject (FinalGrade removed)
                cur.execute(
                    """
                    INSERT INTO Subject 
                    (GradeID, SubjectName, Credits, Marks, Preference,
                     MainCategory, CourseName, CustomCourseName)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        grade_id,
                        name,
                        credits,
                        marks,
                        preference,
                        main_category,
                        course_name,
                        custom_course_name
                    )
                )

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"status": "success", "message": "Transcript saved successfully."})

    except Exception as e:
        print("FULL ERROR:", repr(e))
        return jsonify({"status": "error", "message": "Server error: " + repr(e)}), 500




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



#404 error page
@app.errorhandler(404)
def not_found(error):
    return render_template("404.html.jinja"), 404




#Update-------------------------------------

@app.route("/student/gpa_settings", methods=["GET"])
@login_required
def get_gpa_settings():
    if current_user.role != "student":
        abort(403)

    conn = connect_db()
    cur = conn.cursor()

    # Find StudentProfile
    cur.execute("SELECT ID FROM StudentProfile WHERE UserID = %s", (current_user.id,))
    profile = cur.fetchone()

    if not profile:
        cur.close()
        conn.close()
        return jsonify({"status": "error", "message": "Student profile not found"}), 400

    student_profile_id = profile["ID"]

    # Load GPA settings
    cur.execute("""
        SELECT * FROM GPA_Settings
        WHERE UserID = %s
        ORDER BY UpdatedAt DESC
        LIMIT 1
    """, (current_user.id,))
    settings = cur.fetchone()

    # If no settings exist → return defaults
    if not settings:
        default_settings = {
            "System": "us_4",
            "MaxGPA": 4.00,
            "ScaleJSON": {},
            "WeightingJSON": {}
        }
        cur.close()
        conn.close()
        return jsonify(default_settings)

    # Convert JSON fields
    settings["ScaleJSON"] = json.loads(settings["ScaleJSON"])
    settings["WeightingJSON"] = json.loads(settings["WeightingJSON"])

    cur.close()
    conn.close()

    return jsonify(settings)



@app.route("/student/gpa_settings", methods=["POST"])
@login_required
def save_gpa_settings():
    if current_user.role != "student":
        abort(403)
    
    cur.execute("SELECT ID FROM StudentProfile WHERE UserID = %s", (current_user.id,))
    profile = cur.fetchone()

    if not profile:
        abort(403)

    data = request.get_json()

    if not data:
        return jsonify({"status": "error", "message": "No data received"}), 400

    system = data.get("System")
    max_gpa = data.get("MaxGPA")
    scale_json = json.dumps(data.get("ScaleJSON", {}))
    weighting_json = json.dumps(data.get("WeightingJSON", {}))

    conn = connect_db()
    cur = conn.cursor()

    # Insert new settings row (we keep history)
    cur.execute("""
        INSERT INTO GPA_Settings (UserID, System, MaxGPA, ScaleJSON, WeightingJSON)
        VALUES (%s, %s, %s, %s, %s)
    """, (current_user.id, system, max_gpa, scale_json, weighting_json))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"status": "success", "message": "GPA settings saved successfully."})



