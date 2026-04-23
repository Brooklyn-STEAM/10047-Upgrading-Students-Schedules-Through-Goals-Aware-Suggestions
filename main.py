from flask import Flask, render_template, request, flash, redirect, abort
from flask_login import LoginManager, login_user, current_user, logout_user, login_required, current_user

from flask import request, redirect, url_for, flash
from flask_login import current_user
from flask import jsonify

from werkzeug.utils import secure_filename


import os
import pymysql
from dynaconf import Dynaconf
import json


from course_assigner import (
    compute_category_scores,
    recommend_courses_hybrid,
    suggest_tracks,
)

app = Flask(__name__)

UPLOAD_FOLDER = "static/profile_pics"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.context_processor
def inject_notification_count():
    if current_user.is_authenticated and current_user.role == "student":
        connection = connect_db()
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        # 🔔 Normal notifications
        cursor.execute("""
            SELECT COUNT(*) AS count
            FROM Notification
            WHERE StudentID = %s AND Seen = FALSE
        """, (current_user.id,))
        notif_count = cursor.fetchone()["count"]

        # ❌ Declined notifications
        cursor.execute("""
            SELECT COUNT(*) AS count
            FROM Declined
            WHERE StudentID = %s AND Seen = FALSE
        """, (current_user.id,))
        declined_count = cursor.fetchone()["count"]

        connection.close()

        total = notif_count + declined_count

        return dict(notification_count=total)

    return dict(notification_count=0)

@app.context_processor
def inject_counselor_notification_count():
    if current_user.is_authenticated and current_user.role == "counselor":
        connection = connect_db()
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        cursor.execute("""
            SELECT COUNT(*) AS count
            FROM CounselorNotification
            WHERE CounselorID = %s AND Seen = FALSE
        """, (current_user.id,))

        result = cursor.fetchone()
        count = result["count"] if result else 0

        connection.close()

        return dict(counselor_notification_count=count)

    return dict(counselor_notification_count=0)

@app.context_processor
def inject_navbar_profile():
    profile = None
    if current_user.is_authenticated:
        connection = connect_db()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        try:
            if current_user.role == "student":
                cursor.execute("SELECT ProfilePicture FROM StudentProfile WHERE UserID=%s", (current_user.id,))
                profile = cursor.fetchone()
            elif current_user.role == "counselor":
                cursor.execute("SELECT ProfilePicture FROM CounselorProfile WHERE UserID=%s", (current_user.id,))
                profile = cursor.fetchone()
        except Exception as e:
            print("Navbar profile fetch error:", e)
        finally:
            cursor.close()
            connection.close()
    return dict(navbar_profile=profile) 

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


@app.route("/api/course-assigner/calculate", methods=["POST"])
def calculate_course_assigner():
    data = request.get_json()

    # Extract payload
    transcript = data.get("transcript", {})
    letter_scale = data.get("letterScale", [])
    curriculum = data.get("curriculum", "USA")

    # 1. Compute category scores
    category_scores = compute_category_scores(transcript, letter_scale)

    # 2. Curriculum‑aware hybrid recommender
    top_categories, recommended_hs, recommended_college = recommend_courses_hybrid(
        transcript,
        category_scores,
        curriculum=curriculum
    )

    # 3. Track suggestions (must use category_scores, not top_categories)
    suggested_tracks = suggest_tracks(category_scores)

    # 4. Return everything to frontend
    return jsonify({
        "categoryScores": category_scores,
        "topCategories": top_categories,
        "recommendedHighSchoolCourses": recommended_hs,
        "recommendedCollegeCourses": recommended_college,
        "suggestedTracks": suggested_tracks
    })





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
            SELECT * 
            FROM StudentProfile 
            WHERE UserID = %s
            ORDER BY ID DESC
            LIMIT 1
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

    # Fetch existing profile
    profile = None
    if current_user.role == "student":
        cursor.execute("SELECT *  FROM StudentProfile  WHERE UserID = %s ORDER BY ID DESC LIMIT 1", (current_user.id,))
        profile = cursor.fetchone()
    elif current_user.role == "counselor":
        cursor.execute("SELECT * FROM CounselorProfile WHERE UserID=%s", (current_user.id,))
        profile = cursor.fetchone()

    if request.method == 'POST':
        # --- Update User table ---
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()

        if not name or not email:
            flash("Name and email are required.", "danger")
            return render_template("editmyprofile.html.jinja", profile=profile)

        cursor.execute("""
            UPDATE `User`
            SET Name=%s, Email=%s
            WHERE ID=%s
        """, (name, email, current_user.id))

        # --- Update role-specific profile ---
        if current_user.role == "student":
            phone = request.form.get("phone", "").strip()
            address = request.form.get("address", "").strip()
            bio = request.form.get("bio", "").strip()

            cursor.execute("""
                UPDATE StudentProfile
                SET Phone=%s, Address=%s, Bio=%s
                WHERE UserID=%s
            """, (phone, address, bio, current_user.id))

        elif current_user.role == "counselor":
            phone = request.form.get("phone", "").strip()
            office = request.form.get("office", "").strip()
            office_hours = request.form.get("office_hours", "").strip()
            bio = request.form.get("bio", "").strip()

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

        # --- Handle profile picture ---
        file = request.files.get("profile_picture")
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            try:
                os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
            except FileExistsError:
                flash("Upload folder exists as a file. Please fix the directory.", "danger")
                cursor.close()
                connection.close()
                return redirect(url_for("edit_profile"))

            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)

            # Update profile picture in DB
            if current_user.role == "student":
                cursor.execute("""
                    UPDATE StudentProfile
                    SET ProfilePicture=%s
                    WHERE UserID=%s
                """, (filename, current_user.id))
            elif current_user.role == "counselor":
                cursor.execute("""
                    UPDATE CounselorProfile
                    SET ProfilePicture=%s
                    WHERE UserID=%s
                """, (filename, current_user.id))

        # --- Commit and close ---
        connection.commit()
        cursor.close()
        connection.close()

        # Redirect to your profile page
        return redirect(url_for("myprofile"))

    # GET request
    connection.commit()
    cursor.close()
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

    counselor_decision = None
    counselor_email = None
    counselor_name = None
    counselor_id = None  # 🔥 ADD THIS

    # -----------------------------
    # 🔥 GET CURRENT COUNSELOR (REAL SOURCE)
    # -----------------------------
    cursor.execute("""
        SELECT CounselorUserID
        FROM CounselorStudent
        WHERE StudentUserID = %s
        ORDER BY ID DESC
        LIMIT 1
    """, (current_user.id,))

    row = cursor.fetchone()

    if row:
        counselor_id = row["CounselorUserID"]

        # get counselor info
        cursor.execute("""
            SELECT Name, Email
            FROM User
            WHERE ID = %s
        """, (counselor_id,))

        counselor = cursor.fetchone()

        if counselor:
            counselor_name = counselor["Name"]
            counselor_email = counselor["Email"]

    # -----------------------------
    # OPTIONAL: recommendation status
    # -----------------------------
    cursor.execute("""
        SELECT Status
        FROM Recommendation
        WHERE UserID = %s
        ORDER BY ID DESC
        LIMIT 1
    """, (current_user.id,))

    result = cursor.fetchone()

    if result:
        counselor_decision = result["Status"]

    # -----------------------------
    # STUDENT PROFILE
    # -----------------------------
    cursor.execute("""
        SELECT *
        FROM StudentProfile
        WHERE UserID = %s
    """, (current_user.id,))

    student = cursor.fetchone()

    if not student:
        student = {
            "Grade": "N/A",
            "GPA": "N/A",
            "Attendance": "N/A",
            "Next_Class": "N/A",
            "Next_Assignment": "N/A",
            "AllowCounselorEdit": 0
        }

    # -----------------------------
    # COURSES
    # -----------------------------
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
        counselor_email=counselor_email,
        counselor_decision=counselor_decision,
        counselor_id=counselor_id   # 🔥 THIS FIXES EVERYTHING
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
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    # -----------------------------------
    # 1. Get counselor + status (SOURCE OF TRUTH)
    # -----------------------------------
    cursor.execute("""
        SELECT 
            Recommendation.CounselorID,
            Recommendation.Status,
            User.Name
        FROM Recommendation
        LEFT JOIN User ON Recommendation.CounselorID = User.ID
        WHERE Recommendation.UserID = %s
        LIMIT 1
    """, (current_user.id,))

    row = cursor.fetchone()

    counselor_id = None
    counselor_name = None
    counselor_status = None

    if row:
        counselor_id = row["CounselorID"]
        counselor_name = row["Name"]
        counselor_status = row["Status"]

    # -----------------------------------
    # 2. Load recommendations (ONLY if accepted)
    # -----------------------------------
    information = []

    if counselor_status == "accepted":
        cursor.execute("""
            SELECT Application.*, User.Name
            FROM Application
            JOIN User ON Application.UserID = User.ID
            WHERE Application.StudentUserID = %s
              AND Application.UserID = %s
        """, (current_user.id, counselor_id))

        information = cursor.fetchall()

    # -----------------------------------
    # 3. Close DB
    # -----------------------------------
    cursor.close()
    connection.close()

    # -----------------------------------
    # 4. Render
    # -----------------------------------
    return render_template(
        "recommendation.html.jinja",
        counselor_id=counselor_id,
        counselor_name=counselor_name,
        counselor_status=counselor_status,
        information=information
    )

@app.route("/student/notifications")
@login_required
def student_notifications():
    if current_user.role != "student":
        abort(403)

    connection = connect_db()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    # ✅ 1. Mark ALL as seen (Notification)
    cursor.execute("""
        UPDATE Notification
        SET Seen = TRUE
        WHERE StudentID = %s AND Seen = FALSE
    """, (current_user.id,))

    # ✅ 2. Mark ALL as seen (Declined)
    cursor.execute("""
        UPDATE Declined
        SET Seen = TRUE
        WHERE StudentID = %s AND Seen = FALSE
    """, (current_user.id,))

    connection.commit()

    # ✅ 3. Get normal notifications
    cursor.execute("""
        SELECT 
            ID,
            Type,
            Message,
            CreatedAt,
            'normal' AS Source
        FROM Notification
        WHERE StudentID = %s
    """, (current_user.id,))
    notifications = cursor.fetchall()

    # ✅ 4. Get declined notifications
    cursor.execute("""
        SELECT 
            ID,
            'declined' AS Type,
            Reason AS Message,
            CreatedAt,
            'declined' AS Source
        FROM Declined
        WHERE StudentID = %s
    """, (current_user.id,))
    declined = cursor.fetchall()

    connection.close()

    # ✅ 5. Merge + sort by date
    all_notifications = notifications + declined
    all_notifications.sort(key=lambda x: x["CreatedAt"], reverse=True)

    return render_template(
        "notif.html.jinja",
        notifications=all_notifications
    )

@app.route("/student/notifications/read/<int:notification_id>")
@login_required
def mark_notification_read(notification_id):
    if current_user.role != "student":
        abort(403)

    connection = connect_db()
    cursor = connection.cursor()

    # Only mark if it belongs to the student
    cursor.execute("""
        UPDATE Declined
        SET Seen = TRUE
        WHERE ID = %s AND StudentID = %s
    """, (notification_id, current_user.id))

    connection.commit()
    connection.close()

    return redirect("/student/recommendation")

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

    # ✅ Step 1: Get counselor limit
    cursor.execute("""
        SELECT RequestLimit 
        FROM CounselorProfile 
        WHERE UserID = %s
    """, (counselor_id,))

    row = cursor.fetchone()
    request_limit = row["RequestLimit"] if row else None

    # ✅ Step 2: Count current accepted students
    cursor.execute("""
        SELECT COUNT(*) AS count
        FROM Recommendation
        WHERE CounselorID = %s AND Status = 'accepted'
    """, (counselor_id,))

    accepted_count = cursor.fetchone()["count"]

    # 🚫 Step 3: Block if full
    if request_limit is not None and accepted_count >= request_limit:
        connection.close()
        flash("This counselor is no longer accepting requests.", "danger")
        return redirect("/student/recommendation/addcounselor")

    # ✅ Step 4: (optional but SMART) prevent duplicate request
    cursor.execute("""
        SELECT 1 FROM Recommendation
        WHERE UserID = %s AND CounselorID = %s
    """, (current_user.id, counselor_id))

    if cursor.fetchone():
        connection.close()
        flash("You have already requested this counselor.", "warning")
        return redirect("/student/recommendation")

    # ✅ Step 5: Insert normally
    cursor.execute("""
        INSERT INTO CounselorStudent (CounselorUserID, StudentUserID)
        VALUES (%s, %s)
    """, (counselor_id, current_user.id))

    cursor.execute("""
        INSERT INTO Recommendation (Grade, Comments, UserID, CounselorID)
        VALUES (%s, %s, %s, %s)
    """, (grade, comments, current_user.id, counselor_id))

    cursor.execute("""
        INSERT INTO CounselorNotification 
        (CounselorID, StudentID, Type, Message)
        VALUES (%s, %s, %s, %s)
    """, (
        counselor_id,
        current_user.id,
        "request",
        f"{current_user.name} requested you as a counselor"
    ))

    connection.commit()
    connection.close()

    flash("Counselor requested successfully! Please wait for their response.", "success")
    return redirect("/student/dashboard")


@app.route("/student/recommendation/editrecommendations")
@login_required
def review_recommendation():
    connection = connect_db()
    cursor = connection.cursor()
    cursor.execute("""
    SELECT 
    Recommendation.*, 
    student.Name AS StudentName,
    counselor.Name AS CounselorName
    FROM Recommendation
    JOIN User AS student 
    ON Recommendation.UserID = student.ID
    LEFT JOIN User AS counselor 
    ON Recommendation.CounselorID = counselor.ID
    WHERE Recommendation.UserID = %s
    """, (current_user.id,))
    information = cursor.fetchall()
    connection.close()
    return render_template("edit.html.jinja" , information=information)

@app.route("/student/recommendation/deleterecommendation", methods=["POST"])
@login_required
def delete_recommendation():

    connection = connect_db()
    cursor = connection.cursor()

    recommendation_id = request.form.get("id")

    # 1. Delete recommendation
    cursor.execute("""
        DELETE FROM Recommendation
        WHERE ID = %s AND UserID = %s
    """, (recommendation_id, current_user.id))

    # 2. Optional: remove counselor relationship
    cursor.execute("""
        DELETE FROM CounselorStudent
        WHERE StudentUserID = %s
    """, (current_user.id,))

    connection.commit()
    cursor.close()
    connection.close()

    flash("Recommendation deleted successfully.", "success")
    return redirect("/student/recommendation")

@app.route("/student/recommendation/edit/<id>")
@login_required
def edit_specific_recommendation(id):
    connection = connect_db()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    cursor.execute("""
    SELECT ID, Name, Email FROM User
    WHERE Role='counselor'
    """)
    recommendation = cursor.fetchall()

    cursor.execute("""
    SELECT * FROM Recommendation WHERE UserID = %s
    """, (current_user.id,))
    user = cursor.fetchone()


    connection.close()

    if not recommendation:
        abort(404)

    return render_template("editspecific.html.jinja", recommendation=recommendation , user=user)

@app.route("/student/recommendation/edit/<id>/processing", methods=["POST"])
@login_required
def edit_specific_recommendation_processing(id):
    counselor_id = request.form["counselor_id"]
    grade = request.form["grade"]
    comments = request.form.get("comments")

    connection = connect_db()
    cursor = connection.cursor()

    # Update student profile counselor
    cursor.execute("""
        UPDATE Recommendation
        SET CounselorID = %s, Grade = %s, Comments = %s
        WHERE ID = %s AND UserID = %s
    """, (counselor_id, grade, comments, id, current_user.id))

    connection.commit()
    connection.close()

    flash("Recommendation updated successfully!", "success")
    return redirect("/student/recommendation/editrecommendations")

#dashboard for counselors.
@app.route("/counselor/dashboard")
@login_required
def counselor_dashboard():
    if current_user.role != "counselor":
        abort(404)
    
    connection = connect_db()

    cursor = connection.cursor(pymysql.cursors.DictCursor)

    cursor.execute("""
    SELECT 
        Recommendation.*,
        User.*,
        StudentProfile.ID AS student_profile_id
    FROM Recommendation
    JOIN User ON Recommendation.UserID = User.ID
    JOIN StudentProfile ON StudentProfile.UserID = User.ID
    WHERE CounselorID = %s
    """, (current_user.id,))

    result = cursor.fetchall()

    cursor.execute("""
    SELECT RequestLimit 
    FROM CounselorProfile 
    WHERE UserID = %s
    """, (current_user.id,))

    row = cursor.fetchone()
    request_limit = row["RequestLimit"] if row else None

    connection.close()

    return render_template(
    "counselor_dashboard.html.jinja",
    user=result,
    request_limit=request_limit
)

@app.route("/counselor/set_request_limit", methods=["POST"])
@login_required
def set_request_limit():
    if current_user.role != "counselor":
        abort(403)

    limit = request.form.get("limit")

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE CounselorProfile
        SET RequestLimit = %s
        WHERE UserID = %s
    """, (limit, current_user.id))

    conn.commit()
    conn.close()

    return redirect("/counselor/dashboard")

@app.route("/counselorprofile/<int:counselor_id>")
@login_required
def counselor_profile(counselor_id):

    connection = connect_db()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    # Get counselor profile (from URL)
    cursor.execute("""
        SELECT cp.*, u.Name, u.Email
        FROM CounselorProfile cp
        JOIN User u ON u.ID = cp.UserID
        WHERE cp.UserID = %s
    """, (counselor_id,))

    profile = cursor.fetchone()

    # Get student's assigned counselor (DO NOT overwrite route variable)
    cursor.execute("""
        SELECT CounselorUserID
        FROM StudentProfile
        WHERE UserID = %s
    """, (current_user.id,))

    row = cursor.fetchone()
    student_counselor_id = row["CounselorUserID"] if row else None

    connection.close()

    if not profile:
        return "Counselor not found", 404

    return render_template(
        "counselorprofile.html.jinja",
        profile=profile,
        counselor_id=counselor_id,
        student_counselor_id=student_counselor_id
    )


@app.route("/counselor/dashboard/<int:student_profile_id>")
@login_required
def student_profile(student_profile_id):
    if current_user.role != "counselor":
        abort(403)

    connection = connect_db()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    # Ensure the counselor can view this student
    cursor.execute("""
        SELECT 1 
        FROM StudentProfile sp
        JOIN Recommendation cs ON cs.UserID = sp.UserID
        WHERE cs.CounselorID = %s AND sp.ID = %s
    """, (current_user.id, student_profile_id))
    allowed = cursor.fetchone()
    if not allowed:
        connection.close()
        abort(403)

    # Fetch student info
    cursor.execute("""
        SELECT 
        sp.ID AS student_profile_id,
        u.ID AS user_id,
        u.Name,
        u.Email,
        sp.ProfilePicture,
        sp.Grade,
        sp.Phone,
        sp.Address,
        sp.Bio,
        sp.CounselorNotes
        FROM StudentProfile sp
        JOIN User u ON sp.UserID = u.ID
        WHERE sp.ID = %s
    """, (student_profile_id,))

    student = cursor.fetchone()
    print("STUDENT DATA:", student)  # <-- Debug in terminal

    connection.close()
    return render_template("studentprofile.html.jinja", student=student)

@app.route("/counselor/dashboard/<int:student_profile_id>/notes", methods=["POST"])
@login_required
def save_counselor_notes(student_profile_id):
    if current_user.role != "counselor":
        abort(403)

    notes = request.form.get("notes", "")

    connection  = connect_db()
    cursor = connection.cursor()
    # Optional: verify counselor-student relationship
    cursor.execute("""
        SELECT 1 FROM StudentProfile sp
        JOIN CounselorStudent cs ON cs.StudentUserID = sp.UserID
        WHERE cs.CounselorUserID = %s AND sp.ID = %s
    """, (current_user.id, student_profile_id))
    if not cursor.fetchone():
        cursor.close()
        connection.close()
        abort(403)

    cursor.execute("""
        UPDATE StudentProfile
        SET CounselorNotes = %s
        WHERE ID = %s
    """, (notes, student_profile_id))
    connection.commit()
    cursor.close()
    connection.close()

    return redirect(f"/counselor/dashboard/{student_profile_id}")

@app.route("/counselor/notifications")
@login_required
def counselor_notifications():
    if current_user.role != "counselor":
        abort(403)

    connection = connect_db()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    # ✅ Mark notifications as seen
    cursor.execute("""
        UPDATE CounselorNotification
        SET Seen = TRUE
        WHERE CounselorID = %s AND Seen = FALSE
    """, (current_user.id,))
    connection.commit()

    # ✅ Fetch notifications (MATCHES TEMPLATE EXACTLY)
    cursor.execute("""
        SELECT 
            cn.ID,
            cn.Type,
            cn.Message,
            cn.CreatedAt AS Date,
            u.Name AS StudentName,
            r.Grade,
            r.Comments,
            NULL AS Major  -- placeholder (for template compatibility)
        FROM CounselorNotification cn
        JOIN User u 
            ON cn.StudentID = u.ID
        LEFT JOIN Recommendation r 
            ON r.UserID = cn.StudentID 
           AND r.CounselorID = cn.CounselorID
        WHERE cn.CounselorID = %s
        ORDER BY cn.CreatedAt DESC
    """, (current_user.id,))

    notifications = cursor.fetchall()

    connection.close()

    return render_template(
        "notif2.html.jinja",
        notifications=notifications
    )

@app.route("/counselor/recommendation")
@login_required
def counselor_recommendations():
    if current_user.role != "counselor":
        abort(404)
    
    connection = connect_db()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    # ✅ ONLY accepted students
    cursor.execute("""
        SELECT 
            Recommendation.*, 
            User.Name AS StudentName,
            User.Email AS StudentEmail
        FROM Recommendation
        JOIN User ON Recommendation.UserID = User.ID
        WHERE Recommendation.CounselorID = %s
        AND Recommendation.Status = 'accepted'
    """, (current_user.id,))
    
    students = cursor.fetchall()

    # Attach applications
    for student in students:
        cursor.execute("""
            SELECT *
            FROM Application
            WHERE StudentUserID = %s
              AND UserID = %s
            ORDER BY Date DESC
        """, (student["UserID"], current_user.id))
        
        student["applications"] = cursor.fetchall()
        student["application_count"] = len(student["applications"])

    connection.close()

    return render_template(
        "counselorrecommendation.html.jinja",
        user=students
    )

@app.route("/counselor/dashboard/accept/<int:user_id>")
@login_required
def accept_student(user_id):
    if current_user.role != "counselor":
        abort(403)

    connection = connect_db()
    cursor = connection.cursor()

    # ✅ Step 1: Verify request exists and is pending
    cursor.execute("""
        SELECT *
        FROM Recommendation
        WHERE UserID = %s 
          AND CounselorID = %s
          AND Status = 'pending'
    """, (user_id, current_user.id))

    request = cursor.fetchone()

    if not request:
        connection.close()
        abort(404)

    # ✅ Step 2: Get counselor request limit
    cursor.execute("""
        SELECT RequestLimit 
        FROM CounselorProfile 
        WHERE UserID = %s
    """, (current_user.id,))

    row = cursor.fetchone()
    request_limit = row["RequestLimit"] if row else None

    # ✅ Step 3: Count accepted students
    cursor.execute("""
        SELECT COUNT(*) AS count
        FROM Recommendation
        WHERE CounselorID = %s AND Status = 'accepted'
    """, (current_user.id,))

    accepted_count = cursor.fetchone()["count"]

    # 🚫 Step 4: Enforce limit
    if request_limit is not None and accepted_count >= request_limit:
        connection.close()
        flash("You have reached your maximum student limit.", "danger")
        return redirect("/counselor/dashboard")

    # ✅ Step 5: Accept student
    cursor.execute("""
        UPDATE Recommendation
        SET Status = 'accepted'
        WHERE UserID = %s AND CounselorID = %s
    """, (user_id, current_user.id))

    # 🔔 Step 6: Notify student
    cursor.execute("""
        INSERT INTO Notification (StudentID, CounselorID, Type, Message, Seen)
        VALUES (%s, %s, 'accepted', %s, FALSE)
    """, (
        user_id,
        current_user.id,
        "You have been accepted by your counselor."
    ))

    connection.commit()
    connection.close()

    return redirect("/counselor/dashboard")

@app.route("/counselor/dashboard/decline/<int:user_id>")
@login_required
def decline_academic_record(user_id):
    if current_user.role != "counselor":
        abort(403)

    connection = connect_db()
    cursor = connection.cursor()

    # Get student name + verify relationship
    cursor.execute("""
        SELECT User.Name
        FROM StudentProfile
        JOIN User ON StudentProfile.UserID = User.ID
        WHERE StudentProfile.UserID = %s
    """, (user_id,))

    rc = cursor.fetchone()
    connection.close()

    if not rc:
        abort(404)

    return render_template(
        "decline.html.jinja",
        user_id=user_id,
        student_name=rc["Name"]
    )

@app.route("/counselor/dashboard/decline/<int:user_id>/processing", methods=["POST"])
@login_required
def decline_academic_record_processing(user_id):
    if current_user.role != "counselor":
        abort(403)

    connection = connect_db()
    cursor = connection.cursor()

    # Step 1: Verify student belongs to counselor
    cursor.execute("""
        SELECT UserID
        FROM StudentProfile
        WHERE UserID = %s AND CounselorUserID = %s
    """, (user_id, current_user.id))

    student = cursor.fetchone()

    # Step 2: Get reason
    reason = request.form.get("reason", "")

    # Step 3: Insert into Declined
    cursor.execute("""
        INSERT INTO Declined (UserID, StudentID, Reason)
        VALUES (%s, %s, %s)
    """, (current_user.id, user_id, reason))

    # Step 4: Delete from Recommendation
    cursor.execute("""
        DELETE FROM Recommendation
        WHERE CounselorID = %s AND UserID = %s
    """, (current_user.id, user_id))

    # ✅ NEW: Delete from CounselorStudent
    cursor.execute("""
        DELETE FROM CounselorStudent
        WHERE CounselorUserID = %s AND StudentUserID = %s
    """, (current_user.id, user_id))

    # OPTIONAL (recommended): unassign counselor
    cursor.execute("""
        UPDATE StudentProfile
        SET CounselorUserID = NULL
        WHERE UserID = %s
    """, (user_id,))

    connection.commit()
    cursor.close()
    connection.close()

    return redirect("/counselor/dashboard")


# ✅ EDIT
@app.route("/counselor/recommendation/edit/<int:app_id>", methods=["POST"])
@login_required
def edit_application(app_id):
    if current_user.role != "counselor":
        abort(403)

    major = request.form["major"]
    comments = request.form["comments"]

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE Application
        SET Major = %s, Comments = %s
        WHERE ID = %s AND UserID = %s
    """, (major, comments, app_id, current_user.id))

    connection.commit()
    connection.close()

    return redirect("/counselor/recommendation")


# ✅ DELETE (SECURE)
@app.route("/counselor/recommendation/delete/<int:application_id>", methods=["POST"])
@login_required
def delete_application(application_id):
    if current_user.role != "counselor":
        abort(403)

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM Application
        WHERE ID = %s AND UserID = %s
    """, (application_id, current_user.id))

    connection.commit()
    connection.close()

    return redirect("/counselor/recommendation")


@app.route("/student/academic_record")
@login_required
def student_academic_record():
    if current_user.role != "student":
        abort(403)

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("SELECT ID FROM StudentProfile WHERE UserID = %s", (current_user.id,))
    profile = cur.fetchone()

    transcript_data = None

    if profile:
        student_profile_id = profile["ID"]

        cur.execute("""
            SELECT * FROM Transcript
            WHERE StudentID = %s
            ORDER BY CreatedAt DESC LIMIT 1
        """, (student_profile_id,))
        transcript = cur.fetchone()

        if transcript:
            transcript_id = transcript["ID"]

            cur.execute("SELECT * FROM Grade WHERE TranscriptID = %s", (transcript_id,))
            grades = cur.fetchall()

            grade_list = []

            for g in grades:
                grade_id = g["ID"]

                cur.execute("""
                    SELECT SubjectName, FinalGrade, Credits, Marks, Preference,
                           MainCategory, CourseName, CustomCourseName
                    FROM Subject
                    WHERE GradeID = %s
                """, (grade_id,))
                subjects = cur.fetchall()

                subject_list = []
                for s in subjects:
                    subject_list.append({
                        "Name": s["SubjectName"],
                        "Letter": s["FinalGrade"],
                        "Credits": float(s["Credits"]) if s["Credits"] is not None else None,
                        "Marks": float(s["Marks"]) if s["Marks"] is not None else None,
                        "Preference": s["Preference"],
                        "MainCategory": s["MainCategory"],
                        "CourseName": s["CourseName"],
                        "CustomCourseName": s["CustomCourseName"]
                    })

                grade_list.append({
                    "GradeLevel": g["GradeLevel"],
                    "GPA": float(g["GPA"]) if "GPA" in g and g["GPA"] is not None else None,
                    "Subjects": subject_list
                })

            transcript_data = {
                "GPA": float(transcript["GPA"]) if transcript["GPA"] is not None else None,
                "Grades": grade_list,
                "Curriculum": transcript.get("Curriculum")
            }


    cur.close()
    conn.close()

    return render_template(
        "student_academic_record.html.jinja",
        transcript_json=json.dumps(transcript_data) if transcript_data else "null"
    )



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

        # insert transcript (you’re using CourseID=NULL, so DB must have CourseID)
        cur.execute(
        "INSERT INTO Transcript (StudentID, CourseID, GPA, Curriculum, CreatedAt) "
        "VALUES (%s, NULL, %s, %s, NOW())",
        (student_profile_id, overall_gpa, data.get("Curriculum"))
    )

        transcript_id = cur.lastrowid

        # insert grades + subjects
        for grade in grades_data:
            grade_level = grade.get("GradeLevel")
            grade_gpa = grade.get("GPA")

            cur.execute(
                "INSERT INTO Grade (TranscriptID, GradeLevel, GPA) VALUES (%s, %s, %s)",
                (transcript_id, grade_level, grade_gpa)
            )
            grade_id = cur.lastrowid

            for subject in grade.get("Subjects", []):
                name = subject.get("Name")
                letter = subject.get("Letter")
                credits = subject.get("Credits")
                marks = subject.get("Marks")
                preference = subject.get("Preference")

                main_category = subject.get("MainCategory")
                course_name = subject.get("CourseName")
                custom_course_name = subject.get("CustomCourseName")

                if course_name == "Other" and not custom_course_name:
                    custom_course_name = name

                cur.execute(
                    """
                    INSERT INTO Subject 
                    (GradeID, SubjectName, FinalGrade, Credits, Marks, Preference,
                     MainCategory, CourseName, CustomCourseName)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        grade_id,
                        name,
                        letter,
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




@app.route("/counselor/recommendation/addapplication/<user_id>")
@login_required
def add_application(user_id):

    if current_user.role != "counselor":
        abort(403)

    connection = connect_db()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    cursor.execute("""
    SELECT * FROM `Recommendation`
    JOIN `User` ON `Recommendation`.`UserID` = `User`.`ID`
    WHERE User.ID = %s AND Recommendation.CounselorID = %s
    """, (user_id, current_user.id))

    result = cursor.fetchone()
    connection.close()

    # 🚨 If student is not assigned → block access
    if not result:
        return redirect("/counselor/recommendation")

    return render_template("addapplication.html.jinja", user=result)

@app.route("/counselor/recommendation/addapplication/<user_id>/adding", methods=['POST'])
@login_required
def adding_app(user_id):

    if current_user.role != "counselor":
        abort(403)

    Major = request.form["Major"]
    Comments = request.form["Comments"]

    connection = connect_db()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    # ✅ Validate ownership
    cursor.execute("""
    SELECT * FROM Recommendation
    WHERE UserID = %s AND CounselorID = %s
    """, (user_id, current_user.id))

    student = cursor.fetchone()

    # 🚨 Block if not allowed
    if not student:
        connection.close()
        abort(403)  # or redirect

    # ✅ Safe insert (use validated user_id)
    cursor.execute("""
        INSERT INTO Application
        (UserID, Major, Comments, StudentUserID)
        VALUES (%s, %s, %s, %s)
    """, (current_user.id, Major, Comments, user_id))

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

    # Ensure counselor-student relationship
    cur.execute("""
        SELECT 1
        FROM CounselorStudent
        WHERE CounselorUserID = %s AND StudentUserID = %s
    """, (current_user.id, student_user_id))
    if not cur.fetchone():
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

        # Load grades
        cur.execute("SELECT * FROM Grade WHERE TranscriptID = %s", (transcript_id,))
        grades = cur.fetchall()

        grade_list = []

        for g in grades:
            grade_id = g["ID"]

            cur.execute("""
                SELECT SubjectName, FinalGrade, Credits, Marks, Preference,
                       MainCategory, CourseName, CustomCourseName
                FROM Subject
                WHERE GradeID = %s
            """, (grade_id,))
            subjects = cur.fetchall()

            subject_list = []
            for s in subjects:
                subject_list.append({
                    "Name": s["SubjectName"],
                    "Letter": s["FinalGrade"],
                    "Credits": float(s["Credits"]) if s["Credits"] is not None else None,
                    "Marks": float(s["Marks"]) if s["Marks"] is not None else None,
                    "Preference": s["Preference"],
                    "MainCategory": s["MainCategory"],
                    "CourseName": s["CourseName"],
                    "CustomCourseName": s["CustomCourseName"]
                })

            grade_list.append({
                "GradeLevel": g["GradeLevel"],
                "GPA": float(g["GPA"]) if "GPA" in g and g["GPA"] is not None else None,
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

    # Validate relationship + permissions
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

    overall_gpa = data.get("GPA")
    grades_data = data.get("Grades", [])

    # Insert new transcript
    cur.execute("""
        INSERT INTO Transcript (StudentID, CourseID, GPA, CreatedAt)
        VALUES (%s, NULL, %s, NOW())
    """, (student_profile_id, overall_gpa))
    transcript_id = cur.lastrowid

    max_grade_level = current_profile_grade

    for grade in grades_data:
        grade_level = grade.get("GradeLevel")
        grade_gpa = grade.get("GPA")

        if grade_level and (max_grade_level is None or grade_level > max_grade_level):
            max_grade_level = grade_level

        cur.execute("""
            INSERT INTO Grade (TranscriptID, GradeLevel, GPA)
            VALUES (%s, %s, %s)
        """, (transcript_id, grade_level, grade_gpa))
        grade_id = cur.lastrowid

        for subject in grade.get("Subjects", []):
            cur.execute("""
                INSERT INTO Subject
                (GradeID, SubjectName, FinalGrade, Credits, Marks, Preference,
                 MainCategory, CourseName, CustomCourseName)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                grade_id,
                subject.get("Name"),
                subject.get("Letter"),
                subject.get("Credits"),
                subject.get("Marks"),
                subject.get("Preference"),
                subject.get("MainCategory"),
                subject.get("CourseName"),
                subject.get("CustomCourseName")
            ))

    # Sync student grade
    cur.execute("""
        UPDATE StudentProfile
        SET Grade = %s
        WHERE ID = %s
    """, (max_grade_level, student_profile_id))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"status": "success", "message": "Transcript updated by counselor."})




@app.route("/chat/<int:user_id>")
@login_required
def chat(user_id):

    conn = connect_db()
    cur = conn.cursor(pymysql.cursors.DictCursor)

    # Get target user
    cur.execute("SELECT Name, Role FROM User WHERE ID = %s", (user_id,))
    target = cur.fetchone()

    if not target:
        conn.close()
        return "User not found", 404

    # -----------------------------------------
    # GET ACTIVE COUNSELOR FROM StudentProfile
    # -----------------------------------------
    if current_user.role == "student":

        cur.execute("""
            SELECT CounselorID
            FROM Recommendation
            WHERE UserID = %s
        """, (current_user.id,))

        row = cur.fetchone()
        active_counselor_id = row["CounselorID"] if row else None

        if active_counselor_id != user_id:
            conn.close()
            return "Not allowed", 403

        other_user_id = user_id

    elif current_user.role == "counselor":

        cur.execute("""
            SELECT 1
            FROM Recommendation
            WHERE UserID = %s AND CounselorID = %s
        """, (user_id, current_user.id))

        if not cur.fetchone():
            conn.close()
            return "Not allowed", 403

        other_user_id = user_id

    else:
        conn.close()
        return "Not allowed", 403

    # -----------------------------------------
    # LOAD MESSAGES (NO CounselorStudent NEEDED)
    # -----------------------------------------
    cur.execute("""
        SELECT 
            m.ID,
            m.SenderID,
            m.ReceiverID,
            m.Content,
            m.CreatedAt,
            u.Name AS SenderName
        FROM Message m
        JOIN User u ON u.ID = m.SenderID
        WHERE 
            (m.SenderID = %s AND m.ReceiverID = %s)
            OR
            (m.SenderID = %s AND m.ReceiverID = %s)
        ORDER BY m.CreatedAt ASC
    """, (current_user.id, other_user_id, other_user_id, current_user.id))

    messages = cur.fetchall()

    conn.close()

    return render_template(
        "chat.html.jinja",
        receiver_id=other_user_id,
        receiver_name=target["Name"],
        receiver_role=target["Role"],
        messages=messages
    )
@app.route("/send_message", methods=["POST"])
@login_required
def send_message():

    receiver_id = int(request.form.get("receiver_id"))
    content = request.form["content"]

    conn = connect_db()
    cur = conn.cursor(pymysql.cursors.DictCursor)

    # -----------------------------------------
    # GET ACTIVE COUNSELOR FROM StudentProfile
    # -----------------------------------------
    if current_user.role == "student":
        cur.execute("""
            SELECT CounselorID
            FROM Recommendation
            WHERE UserID = %s
        """, (current_user.id,))
        row = cur.fetchone()
        counselor_id = row["CounselorID"] if row else None

        if counselor_id != receiver_id:
            conn.close()
            return jsonify({"status": "error", "message": "Not allowed"}), 403

    else:
        cur.execute("""
            SELECT CounselorID
            FROM Recommendation
            WHERE UserID = %s
        """, (receiver_id,))
        row = cur.fetchone()
        counselor_id = row["CounselorID"] if row else None

        if current_user.id != counselor_id:
            conn.close()
            return jsonify({"status": "error", "message": "Not allowed"}), 403

    # -----------------------------------------
    # INSERT MESSAGE
    # -----------------------------------------
    cur.execute("""
        INSERT INTO Message (SenderID, ReceiverID, CounselorID, Content)
        VALUES (%s, %s, %s, %s)
    """, (
        current_user.id,
        receiver_id,
        counselor_id,
        content
    ))

    conn.commit()
    conn.close()

    return jsonify({"status": "success"})

@app.route("/get_messages/<int:user_id>")
@login_required
def get_messages(user_id):

    conn = connect_db()
    cur = conn.cursor(pymysql.cursors.DictCursor)

    # Get active counselor from StudentProfile
    cur.execute("""
        SELECT CounselorID
        FROM Recommendation
        WHERE UserID = %s
    """, (current_user.id if current_user.role == "student" else user_id,))

    row = cur.fetchone()
    counselor_id = row["CounselorID"] if row else None

    cur.execute("""
        SELECT 
            m.ID,
            m.SenderID,
            m.ReceiverID,
            m.Content,
            m.CreatedAt,
            u.Name AS SenderName,
            COALESCE(sp.ProfilePicture, cp.ProfilePicture) AS SenderProfilePicture
        FROM Message m
        JOIN User u ON u.ID = m.SenderID
        LEFT JOIN StudentProfile sp ON sp.UserID = u.ID
        LEFT JOIN CounselorProfile cp ON cp.UserID = u.ID
        WHERE (
            (m.SenderID = %s AND m.ReceiverID = %s)
            OR
            (m.SenderID = %s AND m.ReceiverID = %s)
        )
        AND m.CounselorID = %s
        ORDER BY m.CreatedAt ASC
    """, (
        current_user.id, user_id,
        user_id, current_user.id,
        counselor_id
    ))

    messages = cur.fetchall()
    conn.close()

    return jsonify(messages)
        





#404 error page
@app.errorhandler(404)
def not_found(error):
    return render_template("404.html.jinja"), 404



