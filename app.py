from flask import Flask, render_template, request, jsonify
import sqlite3
from datetime import datetime
import random

app = Flask(__name__)

# ================= DATABASE INIT =================

def init_db():

    conn = sqlite3.connect("parking.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS parking_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vehicle_number TEXT,
        phone_number TEXT,
        token_number INTEGER,
        slot_id TEXT,
        entry_time TEXT,
        exit_time TEXT,
        expected_hours REAL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS parking_slots (
        slot_id TEXT PRIMARY KEY,
        status INTEGER
    )
    """)

    for i in range(1, 21):
        cursor.execute(
            "INSERT OR IGNORE INTO parking_slots VALUES (?, ?)",
            (f"P{i}", 0)
        )

    conn.commit()
    conn.close()

init_db()

# ================= HOME =================

@app.route("/")
def home():

    conn = sqlite3.connect("parking.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM parking_slots")
    slots = cursor.fetchall()

    cursor.execute(
        "SELECT COUNT(*) FROM parking_slots WHERE status=0"
    )

    available = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "index.html",
        slots=slots,
        available=available
    )

# ================= BOOK SLOT =================

@app.route("/book", methods=["POST"])
def book():

    data = request.json

    slot_id = data["slot"]
    vehicle = data["vehicle"]
    phone = data["phone"]
    expected_hours = float(data["hours"])

    conn = sqlite3.connect("parking.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT status FROM parking_slots WHERE slot_id=?",
        (slot_id,)
    )

    status = cursor.fetchone()[0]

    # SLOT ALREADY BOOKED

    if status == 1:
        conn.close()
        return jsonify({"success": False})

    token = random.randint(1000, 9999)

    entry_time = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    # UPDATE SLOT STATUS

    cursor.execute(
        "UPDATE parking_slots SET status=1 WHERE slot_id=?",
        (slot_id,)
    )

    # INSERT RECORD

    cursor.execute("""
    INSERT INTO parking_records
    (
        vehicle_number,
        phone_number,
        token_number,
        slot_id,
        entry_time,
        expected_hours
    )
    VALUES (?, ?, ?, ?, ?, ?)
    """,
    (
        vehicle,
        phone,
        token,
        slot_id,
        entry_time,
        expected_hours
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "token": token
    })

# ================= EXIT VEHICLE =================

@app.route("/exit", methods=["GET", "POST"])
def exit_vehicle():

    if request.method == "POST":

        vehicle = request.form["vehicle"]
        token = request.form["token"]

        conn = sqlite3.connect("parking.db")
        cursor = conn.cursor()

        cursor.execute("""
        SELECT entry_time, slot_id, expected_hours
        FROM parking_records
        WHERE vehicle_number=? 
        AND token_number=? 
        AND exit_time IS NULL
        """, (vehicle, token))

        record = cursor.fetchone()

        # INVALID DETAILS

        if not record:

            conn.close()

            return """
            <h2 style='
                color:white;
                text-align:center;
                margin-top:100px;
                font-family:Segoe UI;
            '>
                Invalid Vehicle or Token Number
            </h2>
            """

        entry_time_str, slot_id, expected_hours = record

        entry_time = datetime.strptime(
            entry_time_str,
            "%Y-%m-%d %H:%M:%S"
        )

        exit_time = datetime.now()

        # CALCULATE HOURS

        actual_hours = (
            exit_time - entry_time
        ).total_seconds() / 3600

        # CALCULATE FINE

        fine = 0

        if actual_hours > expected_hours:
            fine = (
                actual_hours - expected_hours
            ) * 30

        # UPDATE EXIT TIME

        cursor.execute("""
        UPDATE parking_records
        SET exit_time=?
        WHERE vehicle_number=?
        AND token_number=?
        """,
        (
            exit_time.strftime("%Y-%m-%d %H:%M:%S"),
            vehicle,
            token
        ))

        # FREE SLOT

        cursor.execute(
            "UPDATE parking_slots SET status=0 WHERE slot_id=?",
            (slot_id,)
        )

        conn.commit()
        conn.close()

        # EXIT SUMMARY PAGE

        return f"""
<html>

<head>

<title>Exit Summary</title>

<link rel="stylesheet" href="/static/style.css">

<style>

body {{
    background:#050816;
    margin:0;
    font-family:'Segoe UI',sans-serif;
}}

.wrapper {{
    height:100vh;
    display:flex;
    justify-content:center;
    align-items:center;
}}

.summary-card {{
    width:390px;
    background:#0f172a;
    border:1px solid rgba(255,255,255,0.05);
    padding:35px;
    border-radius:22px;
    text-align:center;
    box-shadow:0 10px 35px rgba(0,0,0,0.35);
}}

.summary-card h1 {{
    color:white;
    font-size:30px;
    margin-bottom:25px;
}}

.summary-card p {{
    color:#cbd5e1;
    font-size:16px;
    margin:14px 0;
}}

.fine {{
    margin-top:25px;
    font-size:30px;
    font-weight:700;
    color:#ff7b00;
}}

.btn {{
    display:inline-block;
    margin-top:25px;
    padding:12px 24px;
    border-radius:12px;
    background:linear-gradient(145deg,#ff7b00,#ff9500);
    color:white;
    text-decoration:none;
    font-weight:600;
    transition:0.3s;
}}

.btn:hover {{
    transform:translateY(-2px);
}}

</style>

</head>

<body>

<div class="wrapper">

    <div class="summary-card">

        <h1>Exit Summary</h1>

        <p>
            <strong>Expected Hours:</strong>
            {expected_hours}
        </p>

        <p>
            <strong>Actual Hours:</strong>
            {round(actual_hours, 2)}
        </p>

        <div class="fine">
            Fine: ₹{round(fine, 2)}
        </div>

        <a href="/" class="btn">
            Back to Parking
        </a>

    </div>

</div>

</body>

</html>
"""

    return render_template("exit.html")

# ================= RUN =================

if __name__ == "__main__":
    app.run(debug=True)