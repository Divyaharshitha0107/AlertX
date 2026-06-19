import os
import sqlite3
from datetime import datetime

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for
)

from reportlab.pdfgen import canvas
from yolo_model.detector import detect_video

app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# ---------------- SAVE LOG ---------------- #

def save_log(filename, alert):

    conn = sqlite3.connect(
        "database.db"
    )

    cursor = conn.cursor()

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS logs(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        filename TEXT,

        alert TEXT,

        time TEXT

    )

    """)

    cursor.execute(

        "INSERT INTO logs(filename, alert, time) VALUES (?, ?, ?)",

        (

            filename,

            alert,

            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

        )

    )

    conn.commit()

    conn.close()

    print("Log Saved")


# ---------------- DASHBOARD STATS ---------------- #

def get_dashboard_stats():

    conn = sqlite3.connect(
        "database.db"
    )

    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM logs"
    )

    total_logs = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM logs WHERE alert='High Suspicious'"
    )

    high_alerts = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM logs WHERE alert='Medium Suspicious'"
    )

    medium_alerts = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM logs WHERE alert='Low Suspicious'"
    )

    low_alerts = cursor.fetchone()[0]

    conn.close()

    return (

        total_logs,

        high_alerts,

        medium_alerts,

        low_alerts

    )


# ---------------- SYSTEM STATUS ---------------- #

def get_system_status():

    conn = sqlite3.connect(
        "database.db"
    )

    cursor = conn.cursor()

    cursor.execute(

        "SELECT filename,time FROM logs ORDER BY id DESC LIMIT 1"

    )

    latest = cursor.fetchone()

    conn.close()

    last_detection = (

        latest[0]

        if latest

        else

        "No detections"

    )

    return {

        "system":"Online",

        "database":"Connected",

        "model":"YOLOv8 Active",

        "last_detection":last_detection

    }


# ---------------- ROUTES ---------------- #
@app.route("/logout")
def logout():

    return redirect(
        url_for("login")
    )
@app.route("/")
def splash():

    return render_template(
        "splash.html"
    )


@app.route(
    "/login",
    methods=["GET","POST"]
)

def login():

    if request.method == "POST":

        username = request.form["username"]

        password = request.form["password"]

        saved_user = "alertx_admin"

        saved_pass = "AX@Secure2026!"

        if (

            username == saved_user

            and

            password == saved_pass

        ):

            return redirect(

                url_for("dashboard")

            )

        else:

            return render_template(

                "login.html",

                error="Invalid Credentials"

            )

    return render_template(

        "login.html"

    )


@app.route("/dashboard")
def dashboard():

    total_logs, high_alerts, medium_alerts, low_alerts = get_dashboard_stats()

    status = get_system_status()

    return render_template(

        "dashboard.html",

        total_logs=total_logs,

        high_alerts=high_alerts,

        medium_alerts=medium_alerts,

        low_alerts=low_alerts,

        status=status

    )


# ---------------- ALERTS ---------------- #

@app.route("/alerts")
def alerts():

    conn = sqlite3.connect(
        "database.db"
    )

    cursor = conn.cursor()

    cursor.execute(

        "SELECT filename, alert, time FROM logs ORDER BY id DESC"

    )

    alerts_data = cursor.fetchall()

    conn.close()

    return render_template(

        "alerts.html",

        alerts=alerts_data

    )


# ---------------- SETTINGS ---------------- #

@app.route("/settings")
def settings():

    return render_template(
        "settings.html"
    )


# ---------------- CAMERAS ---------------- #

@app.route("/cameras")
def cameras():

    uploaded = os.listdir(
        "static/uploads"
    )

    return render_template(

        "cameras.html",

        uploaded=uploaded

    )


# ---------------- LOGS ---------------- #

@app.route("/logs")
def logs():

    conn = sqlite3.connect(
        "database.db"
    )

    cursor = conn.cursor()

    cursor.execute(

        "SELECT filename, alert, time FROM logs ORDER BY id DESC"

    )

    data = cursor.fetchall()

    conn.close()

    return render_template(

        "logs.html",

        logs=data

    )


# ---------------- REPORTS ---------------- #

@app.route("/reports")
def reports():

    return render_template(
        "reports.html"
    )


@app.route("/generate_report")
def generate_report():

    conn = sqlite3.connect(
        "database.db"
    )

    cursor = conn.cursor()

    cursor.execute(

        "SELECT filename, alert, time FROM logs"

    )

    data = cursor.fetchall()

    conn.close()

    pdf_path = "static/reports/report.pdf"

    pdf = canvas.Canvas(
        pdf_path
    )

    y = 800

    pdf.drawString(

        230,

        820,

        "AlertX Report"

    )

    for row in data:

        pdf.drawString(

            40,

            y,

            f"{row[0]} | {row[1]} | {row[2]}"

        )

        y -= 25

    pdf.save()

    return redirect(

        "/static/reports/report.pdf"

    )


# ---------------- VIDEO UPLOAD ---------------- #

@app.route(
    "/upload",
    methods=["POST"]
)

def upload():
    try:
        if "video" not in request.files:
            return render_template(
                "dashboard.html",
                alert="Error: No file provided",
                confidence=0,
                total_logs=get_dashboard_stats()[0],
                high_alerts=get_dashboard_stats()[1],
                medium_alerts=get_dashboard_stats()[2],
                low_alerts=get_dashboard_stats()[3],
                status=get_system_status()
            )

        file = request.files["video"]

        if file.filename == "":
            return render_template(
                "dashboard.html",
                alert="Error: Invalid filename",
                confidence=0,
                total_logs=get_dashboard_stats()[0],
                high_alerts=get_dashboard_stats()[1],
                medium_alerts=get_dashboard_stats()[2],
                low_alerts=get_dashboard_stats()[3],
                status=get_system_status()
            )

        save_path = os.path.join(
            app.config["UPLOAD_FOLDER"],
            file.filename
        )

        file.save(save_path)
        
        print(f"Video saved to: {save_path}")

        alert, confidence = detect_video(
            save_path
        )
        
        print(f"Detection result: {alert}, {confidence}")

        save_log(
            file.filename,
            alert
        )

        video_path = (
            "/static/uploads/" +
            file.filename
        )

        total_logs, high_alerts, medium_alerts, low_alerts = get_dashboard_stats()

        status = get_system_status()

        return render_template(
            "dashboard.html",
            video=video_path,
            alert=alert,
            confidence=confidence,
            total_logs=total_logs,
            high_alerts=high_alerts,
            medium_alerts=medium_alerts,
            low_alerts=low_alerts,
            status=status
        )
    except Exception as e:
        print(f"Upload error: {str(e)}")
        error_msg = f"Error: {str(e)}"
        total_logs, high_alerts, medium_alerts, low_alerts = get_dashboard_stats()
        return render_template(
            "dashboard.html",
            alert=error_msg,
            confidence=0,
            total_logs=total_logs,
            high_alerts=high_alerts,
            medium_alerts=medium_alerts,
            low_alerts=low_alerts,
            status=get_system_status()
        )


if __name__ == "__main__":

    app.run(
        deug=True
    )
