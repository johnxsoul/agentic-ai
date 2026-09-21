from flask import Flask, render_template, request, redirect, Response
import sqlite3
import csv
import io

app = Flask(__name__)


def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            roll_number TEXT NOT NULL,
            department TEXT NOT NULL,
            year TEXT NOT NULL,
            email TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            total_classes INTEGER NOT NULL,
            attended_classes INTEGER NOT NULL,
            percentage REAL NOT NULL,
            category TEXT NOT NULL,
            FOREIGN KEY (student_id) REFERENCES students(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            achievement_type TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            achievement_date TEXT NOT NULL,
            FOREIGN KEY (student_id) REFERENCES students(id)
        )
    """)

    conn.commit()
    conn.close()


@app.route("/")
def home():
    selected_year = request.args.get("year", "")
    selected_department = request.args.get("department", "")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    filters = []
    values = []

    if selected_year:
        filters.append("students.year = ?")
        values.append(selected_year)

    if selected_department:
        filters.append("students.department = ?")
        values.append(selected_department)

    where_clause = ""
    if filters:
        where_clause = "WHERE " + " AND ".join(filters)

    cursor.execute(f"SELECT COUNT(*) FROM students {where_clause}", values)
    total_students = cursor.fetchone()[0]

    cursor.execute(f"""
        SELECT COUNT(*)
        FROM achievements
        JOIN students ON achievements.student_id = students.id
        {where_clause}
    """, values)
    total_achievements = cursor.fetchone()[0]

    cursor.execute(f"""
        SELECT AVG(attendance.percentage)
        FROM attendance
        JOIN students ON attendance.student_id = students.id
        {where_clause}
    """, values)
    average_attendance = cursor.fetchone()[0] or 0

    cursor.execute(f"""
        SELECT COUNT(*)
        FROM attendance
        JOIN students ON attendance.student_id = students.id
        {where_clause}
        {"AND" if where_clause else "WHERE"} attendance.category = 'Excellent'
    """, values)
    excellent_count = cursor.fetchone()[0]

    cursor.execute(f"""
        SELECT COUNT(*)
        FROM attendance
        JOIN students ON attendance.student_id = students.id
        {where_clause}
        {"AND" if where_clause else "WHERE"} attendance.category = 'Average'
    """, values)
    average_count = cursor.fetchone()[0]

    cursor.execute(f"""
        SELECT COUNT(*)
        FROM attendance
        JOIN students ON attendance.student_id = students.id
        {where_clause}
        {"AND" if where_clause else "WHERE"} attendance.category = 'Low'
    """, values)
    low_count = cursor.fetchone()[0]

    total_attendance_records = excellent_count + average_count + low_count

    if total_attendance_records > 0:
        excellent_percent = (excellent_count / total_attendance_records) * 100
        average_percent = (average_count / total_attendance_records) * 100
        low_percent = (low_count / total_attendance_records) * 100
    else:
        excellent_percent = 0
        average_percent = 0
        low_percent = 0

    cursor.execute(f"""
        SELECT students.name, students.roll_number, attendance.percentage
        FROM attendance
        JOIN students ON attendance.student_id = students.id
        {where_clause}
        ORDER BY attendance.percentage DESC
        LIMIT 2
    """, values)
    top_performers = cursor.fetchall()

    cursor.execute(f"""
        SELECT students.name, students.roll_number,
               achievements.achievement_type, achievements.title
        FROM achievements
        JOIN students ON achievements.student_id = students.id
        {where_clause}
        ORDER BY achievements.id DESC
        LIMIT 2
    """, values)
    recent_achievements = cursor.fetchall()

    conn.close()

    return render_template(
        "index.html",
        total_students=total_students,
        total_achievements=total_achievements,
        average_attendance=average_attendance,
        excellent_percent=excellent_percent,
        average_percent=average_percent,
        low_percent=low_percent,
        top_performers=top_performers,
        recent_achievements=recent_achievements,
        selected_year=selected_year,
        selected_department=selected_department
    )
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM students")
    total_students = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM achievements")
    total_achievements = cursor.fetchone()[0]

    cursor.execute("SELECT AVG(percentage) FROM attendance")
    average_attendance = cursor.fetchone()[0]
    if average_attendance is None:
        average_attendance = 0

    cursor.execute("SELECT COUNT(*) FROM attendance WHERE category = 'Excellent'")
    excellent_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM attendance WHERE category = 'Average'")
    average_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM attendance WHERE category = 'Low'")
    low_count = cursor.fetchone()[0]

    total_attendance_records = excellent_count + average_count + low_count

    if total_attendance_records > 0:
        excellent_percent = (excellent_count / total_attendance_records) * 100
        average_percent = (average_count / total_attendance_records) * 100
        low_percent = (low_count / total_attendance_records) * 100
    else:
        excellent_percent = 0
        average_percent = 0
        low_percent = 0

    cursor.execute("""
        SELECT students.name, students.roll_number, attendance.percentage
        FROM attendance
        JOIN students ON attendance.student_id = students.id
        ORDER BY attendance.percentage DESC
        LIMIT 2
    """)
    top_performers = cursor.fetchall()

    cursor.execute("""
        SELECT students.name, students.roll_number,
               achievements.achievement_type, achievements.title
        FROM achievements
        JOIN students ON achievements.student_id = students.id
        ORDER BY achievements.id DESC
        LIMIT 2
    """)
    recent_achievements = cursor.fetchall()

    conn.close()

    return render_template(
        "index.html",
        total_students=total_students,
        total_achievements=total_achievements,
        average_attendance=average_attendance,
        excellent_percent=excellent_percent,
        average_percent=average_percent,
        low_percent=low_percent,
        top_performers=top_performers,
        recent_achievements=recent_achievements
    )


@app.route("/students", methods=["GET", "POST"])
def students():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    if request.method == "POST":
        name = request.form["name"]
        roll_number = request.form["roll_number"]
        department = request.form["department"]
        year = request.form["year"]
        email = request.form["email"]

        cursor.execute("""
            INSERT INTO students (name, roll_number, department, year, email)
            VALUES (?, ?, ?, ?, ?)
        """, (name, roll_number, department, year, email))

        conn.commit()
        conn.close()
        return redirect("/students")

    cursor.execute("SELECT * FROM students ORDER BY name ASC")
    students_data = cursor.fetchall()
    conn.close()

    return render_template("students.html", students=students_data)


@app.route("/attendance", methods=["GET", "POST"])
def attendance():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    if request.method == "POST":
        student_id = request.form["student_id"]
        total_classes = int(request.form["total_classes"])
        attended_classes = int(request.form["attended_classes"])

        percentage = (attended_classes / total_classes) * 100

        if percentage >= 85:
            category = "Excellent"
        elif percentage >= 75:
            category = "Average"
        else:
            category = "Low"

        cursor.execute("""
            INSERT INTO attendance
            (student_id, total_classes, attended_classes, percentage, category)
            VALUES (?, ?, ?, ?, ?)
        """, (student_id, total_classes, attended_classes, percentage, category))

        conn.commit()
        conn.close()
        return redirect("/attendance")

    cursor.execute("SELECT id, name, roll_number FROM students")
    students_data = cursor.fetchall()

    cursor.execute("""
    SELECT attendance.id, students.name, students.roll_number,
           attendance.total_classes, attendance.attended_classes,
           attendance.percentage, attendance.category
    FROM attendance
    JOIN students ON attendance.student_id = students.id
    ORDER BY students.name ASC
""")
    attendance_data = cursor.fetchall()

    conn.close()

    return render_template(
        "attendance.html",
        students=students_data,
        attendance=attendance_data
    )


@app.route("/achievements", methods=["GET", "POST"])
def achievements():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    if request.method == "POST":
        student_id = request.form["student_id"]
        achievement_type = request.form["achievement_type"]
        title = request.form["title"]
        description = request.form["description"]
        achievement_date = request.form["achievement_date"]

        cursor.execute("""
            INSERT INTO achievements
            (student_id, achievement_type, title, description, achievement_date)
            VALUES (?, ?, ?, ?, ?)
        """, (student_id, achievement_type, title, description, achievement_date))

        conn.commit()
        conn.close()
        return redirect("/achievements")

    cursor.execute("SELECT id, name, roll_number FROM students ORDER BY name ASC")
    students_data = cursor.fetchall()

    cursor.execute("""
    SELECT achievements.id, students.name, students.roll_number,
           achievements.achievement_type, achievements.title,
           achievements.description, achievements.achievement_date
    FROM achievements
    JOIN students ON achievements.student_id = students.id
    ORDER BY students.name ASC
""")
    achievements_data = cursor.fetchall()

    conn.close()

    return render_template(
        "achievements.html",
        students=students_data,
        achievements=achievements_data
    )
@app.route("/agent", methods=["GET", "POST"])
def agent():
    response = []
    user_query = ""

    if request.method == "POST":
        user_query = request.form["query"].lower()

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        if "low attendance" in user_query:
            cursor.execute("""
                SELECT students.name, students.roll_number, attendance.percentage, attendance.category
                FROM attendance
                JOIN students ON attendance.student_id = students.id
                WHERE attendance.category = 'Low'
            """)
            response = cursor.fetchall()

        elif "excellent attendance" in user_query:
            cursor.execute("""
                SELECT students.name, students.roll_number, attendance.percentage, attendance.category
                FROM attendance
                JOIN students ON attendance.student_id = students.id
                WHERE attendance.category = 'Excellent'
            """)
            response = cursor.fetchall()

        elif "average attendance" in user_query:
            cursor.execute("""
                SELECT students.name, students.roll_number, attendance.percentage, attendance.category
                FROM attendance
                JOIN students ON attendance.student_id = students.id
                WHERE attendance.category = 'Average'
            """)
            response = cursor.fetchall()

        elif "placed students" in user_query or "placement" in user_query:
            cursor.execute("""
                SELECT students.name, students.roll_number,
                       achievements.title, achievements.description, achievements.achievement_date
                FROM achievements
                JOIN students ON achievements.student_id = students.id
                WHERE achievements.achievement_type = 'Placement'
            """)
            response = cursor.fetchall()

        elif "all achievements" in user_query or "achievements" in user_query:
            cursor.execute("""
                SELECT students.name, students.roll_number,
                       achievements.achievement_type, achievements.title,
                       achievements.description, achievements.achievement_date
                FROM achievements
                JOIN students ON achievements.student_id = students.id
            """)
            response = cursor.fetchall()

        else:
            response = [("Sorry, I could not understand your query.",)]

        conn.close()

    return render_template("agent.html", response=response, query=user_query)
@app.route("/reports")
def reports():
    return render_template("reports.html")


@app.route("/download_attendance_report")
def download_attendance_report():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT students.name, students.roll_number,
               attendance.total_classes, attendance.attended_classes,
               attendance.percentage, attendance.category
        FROM attendance
        JOIN students ON attendance.student_id = students.id
    """)

    data = cursor.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Student Name",
        "Roll Number",
        "Total Classes",
        "Attended Classes",
        "Percentage",
        "Category"
    ])

    writer.writerows(data)

    response = Response(output.getvalue(), mimetype="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=attendance_report.csv"

    return response


@app.route("/download_low_attendance_report")
def download_low_attendance_report():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT students.name, students.roll_number,
               attendance.total_classes, attendance.attended_classes,
               attendance.percentage, attendance.category
        FROM attendance
        JOIN students ON attendance.student_id = students.id
        WHERE attendance.category = 'Low'
    """)

    data = cursor.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Student Name",
        "Roll Number",
        "Total Classes",
        "Attended Classes",
        "Percentage",
        "Category"
    ])

    writer.writerows(data)

    response = Response(output.getvalue(), mimetype="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=low_attendance_report.csv"

    return response


@app.route("/download_achievement_report")
def download_achievement_report():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT students.name, students.roll_number,
               achievements.achievement_type, achievements.title,
               achievements.description, achievements.achievement_date
        FROM achievements
        JOIN students ON achievements.student_id = students.id
    """)

    data = cursor.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Student Name",
        "Roll Number",
        "Achievement Type",
        "Title",
        "Description",
        "Date"
    ])

    writer.writerows(data)

    response = Response(output.getvalue(), mimetype="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=achievement_report.csv"

    return response
@app.route("/edit_student/<int:student_id>", methods=["GET", "POST"])
def edit_student(student_id):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    if request.method == "POST":
        name = request.form["name"]
        roll_number = request.form["roll_number"]
        department = request.form["department"]
        year = request.form["year"]
        email = request.form["email"]

        cursor.execute("""
            UPDATE students
            SET name = ?, roll_number = ?, department = ?, year = ?, email = ?
            WHERE id = ?
        """, (name, roll_number, department, year, email, student_id))

        conn.commit()
        conn.close()
        return redirect("/students")

    cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
    student = cursor.fetchone()
    conn.close()

    return render_template("edit_student.html", student=student)
@app.route("/delete_student/<int:student_id>")
def delete_student(student_id):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM attendance WHERE student_id = ?", (student_id,))
    cursor.execute("DELETE FROM achievements WHERE student_id = ?", (student_id,))
    cursor.execute("DELETE FROM students WHERE id = ?", (student_id,))

    conn.commit()
    conn.close()

    return redirect("/students")
if __name__ == "__main__":
    init_db()
    app.run(debug=True)