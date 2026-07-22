from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = "hospital_secret_key"
DATABASE = "hospital.db"


# -----------------------------
# Database Connection
# -----------------------------
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# -----------------------------
# Create Database
# -----------------------------
def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    # Patients Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS patients(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        age INTEGER,
        gender TEXT,
        phone TEXT,
        address TEXT
    )
    """)

    # Doctors Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS doctors(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        specialization TEXT,
        phone TEXT,
        email TEXT
    )
    """)

    # Appointments Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS appointments(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_name TEXT,
        doctor_name TEXT,
        appointment_date TEXT,
        appointment_time TEXT
    )
    """)

    # Billing Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bills(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_name TEXT,
        treatment TEXT,
        amount REAL,
        payment_status TEXT
    )
    """)

    # Default Admin
    cursor.execute(
        "SELECT * FROM users WHERE username=?",
        ("admin",)
    )
    if cursor.fetchone() is None:
        cursor.execute(
            "INSERT INTO users(username,password) VALUES(?,?)",
            ("admin", "admin123")
        )

    conn.commit()
    conn.close()


# -----------------------------
# Login Page
# -----------------------------
@app.route("/")
def home():
    return render_template("login.html")


# -----------------------------
# Login
# -----------------------------
@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (username, password)
    )
    user = cursor.fetchone()
    conn.close()

    if user:
        session["user"] = username
        return redirect(url_for("dashboard"))

    return render_template(
        "login.html",
        error="Invalid Username or Password"
    )


# -----------------------------
# Logout
# -----------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


# -----------------------------
# Dashboard
# -----------------------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("home"))

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM patients")
    total_patients = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM doctors")
    total_doctors = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM appointments")
    total_appointments = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM bills")
    total_bills = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "dashboard.html",
        total_patients=total_patients,
        total_doctors=total_doctors,
        total_appointments=total_appointments,
        total_bills=total_bills
    )


# -----------------------------
# Patients
# -----------------------------
@app.route("/patients", methods=["GET", "POST"])
def patients():
    if "user" not in session:
        return redirect(url_for("home"))

    conn = get_db()
    cursor = conn.cursor()

    # Add Patient
    if request.method == "POST":
        name = request.form["name"]
        age = request.form["age"]
        gender = request.form["gender"]
        phone = request.form["phone"]
        address = request.form["address"]

        cursor.execute("""
            INSERT INTO patients
            (name, age, gender, phone, address)
            VALUES (?, ?, ?, ?, ?)
        """, (name, age, gender, phone, address))
        conn.commit()
        return redirect(url_for("patients"))

    # Display / Search Patients
    search = request.args.get("search")
    
    if search:
        cursor.execute(
            "SELECT * FROM patients WHERE name LIKE ?",
            ('%' + search + '%',)
        )
    else:
        cursor.execute(
            "SELECT * FROM patients ORDER BY id DESC"
        )
        
    patients = cursor.fetchall()
    conn.close()

    return render_template(
        "patients.html",
        patients=patients
    )


# -----------------------------
# Edit Patient
# -----------------------------
@app.route("/patients/edit/<int:id>", methods=["GET", "POST"])
def edit_patient(id):
    if "user" not in session:
        return redirect(url_for("home"))

    conn = get_db()
    cursor = conn.cursor()

    if request.method == "POST":
        name = request.form["name"]
        age = request.form["age"]
        gender = request.form["gender"]
        phone = request.form["phone"]
        address = request.form["address"]

        cursor.execute("""
            UPDATE patients
            SET
                name=?,
                age=?,
                gender=?,
                phone=?,
                address=?
            WHERE id=?
        """, (name, age, gender, phone, address, id))
        conn.commit()
        conn.close()
        return redirect(url_for("patients"))

    cursor.execute("SELECT * FROM patients WHERE id=?", (id,))
    patient = cursor.fetchone()
    conn.close()

    if patient is None:
        return "Patient Not Found"

    return render_template(
        "patient_edit.html",
        patient=patient
    )


# -----------------------------
# Delete Patient
# -----------------------------
@app.route("/patients/delete/<int:id>")
def delete_patient(id):
    if "user" not in session:
        return redirect(url_for("home"))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM patients WHERE id=?",
        (id,)
    )
    conn.commit()
    conn.close()
    return redirect(url_for("patients"))


# -----------------------------
# Doctors
# -----------------------------
@app.route("/doctors", methods=["GET", "POST"])
def doctors():
    if "user" not in session:
        return redirect(url_for("home"))

    conn = get_db()
    cursor = conn.cursor()

    # Add Doctor
    if request.method == "POST":
        name = request.form["name"]
        specialization = request.form["specialization"]
        phone = request.form["phone"]
        email = request.form["email"]

        cursor.execute("""
        INSERT INTO doctors
        (name, specialization, phone, email)
        VALUES (?, ?, ?, ?)
        """,
        (name, specialization, phone, email))

        conn.commit()
        return redirect(url_for("doctors"))

    # Display / Search Doctors
    search = request.args.get("search")
    
    if search:
        cursor.execute(
            "SELECT * FROM doctors WHERE name LIKE ?",
            ('%' + search + '%',)
        )
    else:
        cursor.execute(
            "SELECT * FROM doctors ORDER BY id DESC"
        )
        
    doctors = cursor.fetchall()
    conn.close()

    return render_template(
        "doctors.html",
        doctors=doctors
    )


# -----------------------------
# Edit Doctor
# -----------------------------
@app.route("/doctors/edit/<int:id>", methods=["GET", "POST"])
def edit_doctor(id):
    if "user" not in session:
        return redirect(url_for("home"))

    conn = get_db()
    cursor = conn.cursor()

    if request.method == "POST":
        name = request.form["name"]
        specialization = request.form["specialization"]
        phone = request.form["phone"]
        email = request.form["email"]

        cursor.execute("""
        UPDATE doctors
        SET
            name=?,
            specialization=?,
            phone=?,
            email=?
        WHERE id=?
        """,
        (name, specialization, phone, email, id))

        conn.commit()
        conn.close()
        return redirect(url_for("doctors"))

    cursor.execute("SELECT * FROM doctors WHERE id=?", (id,))
    doctor = cursor.fetchone()

    conn.close()

    return render_template(
        "doctor_edit.html",
        doctor=doctor
    )


# -----------------------------
# Delete Doctor
# -----------------------------
@app.route("/doctors/delete/<int:id>")
def delete_doctor(id):
    if "user" not in session:
        return redirect(url_for("home"))

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM doctors WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("doctors"))


# -----------------------------
# Appointments
# -----------------------------
@app.route("/appointments", methods=["GET", "POST"])
def appointments():
    if "user" not in session:
        return redirect(url_for("home"))

    conn = get_db()
    cursor = conn.cursor()

    if request.method == "POST":
        patient_name = request.form["patient_name"]
        doctor_name = request.form["doctor_name"]
        appointment_date = request.form["appointment_date"]
        appointment_time = request.form["appointment_time"]

        cursor.execute("""
        INSERT INTO appointments
        (patient_name, doctor_name, appointment_date, appointment_time)
        VALUES (?, ?, ?, ?)
        """,
        (patient_name, doctor_name, appointment_date, appointment_time))

        conn.commit()
        return redirect(url_for("appointments"))

    # Display / Search Appointments
    search = request.args.get("search")
    
    if search:
        cursor.execute("""
            SELECT * FROM appointments
            WHERE patient_name LIKE ?
               OR doctor_name LIKE ?
            ORDER BY id DESC
        """, ('%' + search + '%', '%' + search + '%'))
    else:
        cursor.execute("SELECT * FROM appointments ORDER BY id DESC")
        
    appointments = cursor.fetchall()

    conn.close()

    return render_template(
        "appointments.html",
        appointments=appointments
    )


# -----------------------------
# Edit Appointment
# -----------------------------
@app.route("/appointments/edit/<int:id>", methods=["GET", "POST"])
def edit_appointment(id):
    if "user" not in session:
        return redirect(url_for("home"))

    conn = get_db()
    cursor = conn.cursor()

    if request.method == "POST":
        patient_name = request.form["patient_name"]
        doctor_name = request.form["doctor_name"]
        appointment_date = request.form["appointment_date"]
        appointment_time = request.form["appointment_time"]

        cursor.execute("""
        UPDATE appointments
        SET
            patient_name=?,
            doctor_name=?,
            appointment_date=?,
            appointment_time=?
        WHERE id=?
        """,
        (patient_name, doctor_name, appointment_date, appointment_time, id))

        conn.commit()
        conn.close()
        return redirect(url_for("appointments"))

    cursor.execute("SELECT * FROM appointments WHERE id=?", (id,))
    appointment = cursor.fetchone()

    conn.close()

    return render_template(
        "appointment_edit.html",
        appointment=appointment
    )


# -----------------------------
# Delete Appointment
# -----------------------------
@app.route("/appointments/delete/<int:id>")
def delete_appointment(id):
    if "user" not in session:
        return redirect(url_for("home"))

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM appointments WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("appointments"))


# -----------------------------
# Billing
# -----------------------------
@app.route("/billing", methods=["GET", "POST"])
def billing():
    if "user" not in session:
        return redirect(url_for("home"))

    conn = get_db()
    cursor = conn.cursor()

    if request.method == "POST":
        patient_name = request.form["patient_name"]
        treatment = request.form["treatment"]
        amount = request.form["amount"]
        payment_status = request.form["payment_status"]

        cursor.execute("""
        INSERT INTO bills
        (patient_name, treatment, amount, payment_status)
        VALUES (?, ?, ?, ?)
        """,
        (patient_name, treatment, amount, payment_status))

        conn.commit()
        return redirect(url_for("billing"))

    cursor.execute("SELECT * FROM bills ORDER BY id DESC")
    bills = cursor.fetchall()

    conn.close()

    return render_template(
        "billing.html",
        bills=bills
    )


# -----------------------------
# Reports
# -----------------------------
@app.route("/reports")
def reports():
    if "user" not in session:
        return redirect(url_for("home"))

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM patients")
    total_patients = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM doctors")
    total_doctors = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM appointments")
    total_appointments = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM bills")
    total_bills = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "reports.html",
        total_patients=total_patients,
        total_doctors=total_doctors,
        total_appointments=total_appointments,
        total_bills=total_bills
    )


# -----------------------------
# Run Application
# -----------------------------
if __name__ == "__main__":
    init_db()
    app.run(debug=True)