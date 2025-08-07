from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import os
import sqlite3
from datetime import datetime
from ultralytics import YOLO
import uuid

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['DETECTION_FOLDER'] = 'runs'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['DETECTION_FOLDER'], exist_ok=True)

# Load your trained YOLO model
model = YOLO('best.pt')  # Use the correct path to your model

# Initialize SQLite
def init_db():
    with sqlite3.connect("database.db") as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS detections (
                            id TEXT PRIMARY KEY,
                            filename TEXT,
                            detected_classes TEXT,
                            timestamp TEXT
                        )''')

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analytics')
def analytics():
    with sqlite3.connect("database.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM detections ORDER BY timestamp DESC")
        rows = cursor.fetchall()
    return render_template("analytics.html", rows=rows)

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    if file:
        filename = str(uuid.uuid4()) + "_" + file.filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        results = model(filepath)
        names = model.names
        detected = set()

        for result in results:
            boxes = result.boxes
            for cls in boxes.cls:
                detected.add(names[int(cls)])

        detected_str = ', '.join(detected)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with sqlite3.connect("database.db") as conn:
            conn.execute("INSERT INTO detections (id, filename, detected_classes, timestamp) VALUES (?, ?, ?, ?)",
                         (str(uuid.uuid4()), filename, detected_str, timestamp))

        return redirect(url_for('analytics'))
    return 'No file uploaded.'

if __name__ == '__main__':
    app.run(debug=True)
