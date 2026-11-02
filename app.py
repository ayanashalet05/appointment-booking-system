
import os
import re
from datetime import datetime, timedelta
from functools import wraps

import pymysql
from dotenv import load_dotenv
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash
)
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-this-secret-key")


# -------------------- DATABASE CONNECTION --------------------

def get_db_connection():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "appointment_booking"),
        cursorclass=pymysql.cursors.Cursor,
        autocommit=False
    )


# -------------------- LOGIN PROTECTION --------------------

def patient_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "error")
            return redirect(url_for("patient_login"))
        return function(*args, **kwargs)
    return wrapper


def admin_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if not session.get("admin_logged_in"):
            flash("Please log in as admin.", "error")
            return redirect(url_for("admin_login"))
        return function(*args, **kwargs)
    return wrapper


# -------------------- HOME --------------------

@app.route("/")
def home():
    return render_template("index.html")


# -------------------- PATIENT REGISTRATION --------------------

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not full_name or not email or not password:
            flash("Please fill in all required fields.", "error")
            return redirect(url_for("register"))

        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            flash("Please enter a valid email address.", "error")
            return redirect(url_for("register"))

        if len(password) < 8:
            flash("Password must contain at least 8 characters.", "error")
            return redirect(url_for("register"))

        connection = None
        try:
            connection = get_db_connection()

            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id FROM users WHERE email = %s",
                    (email,)
                )

                if cursor.fetchone():
                    flash("This email is already registered. Please log in.", "error")
                    return redirect(url_for("patient_login"))

                password_hash = generate_password_hash(password)

                cursor.execute(
                    """
                    INSERT INTO users (full_name, email, password_hash)
                    VALUES (%s, %s, %s)
                    """,
                    (full_name, email, password_hash)
                )

            connection.commit()
            flash("Registration successful. Please log in.", "success")
            return redirect(url_for("patient_login"))

        except Exception:
            if connection:
                connection.rollback()
            app.logger.exception("Patient registration failed")
            flash("Registration failed. Please try again.", "error")

        finally:
            if connection:
                connection.close()

    return render_template("register.html")


# -------------------- PATIENT LOGIN --------------------

@app.route("/patient/login", methods=["GET", "POST"])
def patient_login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        connection = None
        try:
            connection = get_db_connection()

            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, full_name, email, password_hash
                    FROM users
                    WHERE email = %s
                    """,
                    (email,)
                )
                user = cursor.fetchone()

            if user and check_password_hash(user[3], password):
                session.clear()
                session["user_id"] = user[0]
                session["user_name"] = user[1]
                session["user_email"] = user[2]

                return redirect(url_for("patient_dashboard"))

            flash("Invalid email or password.", "error")

        except Exception:
            app.logger.exception("Patient login failed")
            flash("Unable to log in. Please try again.", "error")

        finally:
            if connection:
                connection.close()

    return render_template("patient_login.html")


# -------------------- PATIENT DASHBOARD --------------------

@app.route("/patient/dashboard")
@patient_required
def patient_dashboard():
    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, service, appointment_date, appointment_time,
                       phone, name, email
                FROM appointments
                WHERE user_id = %s
                ORDER BY appointment_date DESC, appointment_time DESC
                """,
                (session["user_id"],)
            )
            rows = cursor.fetchall()

        now = datetime.now()
        upcoming = []
        history = []

        for row in rows:
            appointment_date = row[2]
            appointment_time = row[3]

            # PyMySQL may return MySQL TIME as timedelta.
            if isinstance(appointment_time, timedelta):
                total_seconds = int(appointment_time.total_seconds())
                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)

                appointment_time = datetime.min.replace(
                    hour=hours,
                    minute=minutes,
                    second=seconds
                ).time()

            appointment = {
                "id": row[0],
                "service": row[1],
                "date": appointment_date,
                "time": appointment_time,
                "phone": row[4],
                "name": row[5],
                "email": row[6]
            }

            appointment_datetime = datetime.combine(
                appointment_date, appointment_time
            )

            if appointment_datetime >= now:
                upcoming.append(appointment)
            else:
                history.append(appointment)

        upcoming.sort(key=lambda item: (item["date"], item["time"]))
        history.sort(
            key=lambda item: (item["date"], item["time"]),
            reverse=True
        )

        return render_template(
            "patient_dashboard.html",
            user_name=session.get("user_name"),
            upcoming=upcoming,
            history=history
        )

    except Exception:
        app.logger.exception("Could not load patient dashboard")
        return "Could not load your appointments. Please try again.", 500

    finally:
        if connection:
            connection.close()


# -------------------- BOOK APPOINTMENT --------------------

@app.route("/book", methods=["POST"])
@patient_required
def book_appointment():
    service = request.form.get("service", "").strip()
    appointment_date_text = request.form.get("appointment_date", "").strip()
    appointment_time_text = request.form.get("appointment_time", "").strip()
    phone = request.form.get("phone", "").strip()

    if not all([
        service,
        appointment_date_text,
        appointment_time_text,
        phone
    ]):
        flash("Please fill in all appointment fields.", "error")
        return redirect(url_for("patient_dashboard"))

    if not re.fullmatch(r"\d{10}", phone):
        flash("Please enter a valid 10-digit phone number.", "error")
        return redirect(url_for("patient_dashboard"))

    try:
        appointment_datetime = datetime.strptime(
            f"{appointment_date_text} {appointment_time_text}",
            "%Y-%m-%d %H:%M"
        )
    except ValueError:
        flash("Please enter a valid appointment date and time.", "error")
        return redirect(url_for("patient_dashboard"))

    if appointment_datetime <= datetime.now():
        flash("Please choose a future date and time.", "error")
        return redirect(url_for("patient_dashboard"))

    connection = None
    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO appointments
                    (name, email, phone, appointment_date,
                     appointment_time, service, user_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    session["user_name"],
                    session["user_email"],
                    phone,
                    appointment_datetime.date(),
                    appointment_datetime.time(),
                    service,
                    session["user_id"]
                )
            )

        connection.commit()
        flash("Appointment booked successfully!", "success")

    except Exception:
        if connection:
            connection.rollback()
        app.logger.exception("Appointment booking failed")
        flash("Could not book the appointment. Please try again.", "error")

    finally:
        if connection:
            connection.close()

    return redirect(url_for("patient_dashboard"))


# -------------------- PATIENT LOGOUT --------------------

@app.route("/patient/logout", methods=["POST"])
def patient_logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("patient_login"))


# -------------------- ADMIN LOGIN --------------------

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        admin_username = os.getenv("ADMIN_USERNAME", "admin")
        admin_password = os.getenv("ADMIN_PASSWORD", "")

        if (
            admin_password
            and username == admin_username
            and password == admin_password
        ):
            session.clear()
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))

        flash("Invalid admin username or password.", "error")

    return render_template("admin_login.html")


# -------------------- ADMIN DASHBOARD --------------------

@app.route("/admin")
@admin_required
def admin_dashboard():
    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, name, email, phone, appointment_date,
                       appointment_time, service
                FROM appointments
                ORDER BY appointment_date DESC, appointment_time DESC
                """
            )
            rows = cursor.fetchall()

        appointments = []

        for row in rows:
            appointment_time = row[5]

            if isinstance(appointment_time, timedelta):
                total_seconds = int(appointment_time.total_seconds())
                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)

                appointment_time = datetime.min.replace(
                    hour=hours,
                    minute=minutes,
                    second=seconds
                ).time()

            appointments.append({
                "id": row[0],
                "name": row[1],
                "email": row[2],
                "phone": row[3],
                "date": row[4],
                "time": appointment_time,
                "service": row[6]
            })

        return render_template(
            "admin_dashboard.html",
            appointments=appointments
        )

    except Exception:
        app.logger.exception("Could not load admin dashboard")
        return "Could not load admin dashboard. Please try again.", 500

    finally:
        if connection:
            connection.close()


# -------------------- ADMIN LOGOUT --------------------

@app.route("/admin/logout", methods=["POST"])
def admin_logout():
    session.clear()
    flash("Admin logged out successfully.", "success")
    return redirect(url_for("admin_login"))


# -------------------- RUN APPLICATION --------------------

if __name__ == "__main__":
    app.run(debug=True)
