from flask import Flask, render_template, request, redirect, url_for
import os
import sqlite3
from datetime import datetime
import uuid
import json
from io import BytesIO
from werkzeug.utils import secure_filename
from PIL import Image, UnidentifiedImageError

# =============================
# Config section (directly here)
# =============================
UPLOAD_FOLDER = "uploads"
DETECTION_FOLDER = "runs"
DB_NAME = "database.db"

# Allowed file types
ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "bmp", "gif", "tiff", "webp", "jfif"}
ALLOWED_VIDEO_EXTENSIONS = {"mp4", "avi", "mov", "mkv", "webm"}

# Default location (Muzaffarabad, Azad Kashmir)
CITY_NAME = "Muzaffarabad, Azad Kashmir"
CITY_COORDS = (34.3700, 73.4711)

# =============================

# Try to import YOLO
try:
    from ultralytics import YOLO
    model = YOLO("best.pt")  # make sure best.pt is in project root
except Exception as e:
    print("⚠️ Warning: YOLO not loaded:", e)
    model = None

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["DETECTION_FOLDER"] = DETECTION_FOLDER
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["DETECTION_FOLDER"], exist_ok=True)


# ===== DB setup =====
def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS detections (
                id TEXT PRIMARY KEY,
                filename TEXT,
                detected_classes TEXT,
                timestamp TEXT,
                location TEXT,
                incharge TEXT
            )"""
        )
init_db()


# ===== Save uploaded image safely =====
def save_uploaded_image(file_storage):
    raw = file_storage.read()
    try:
        img = Image.open(BytesIO(raw))
        img.verify()
    except (UnidentifiedImageError, Exception):
        raise ValueError("Uploaded file is not a valid image")

    img = Image.open(BytesIO(raw))
    fmt = img.format or "JPEG"
    fmt_lower = fmt.lower()
    ext_map = {"jpeg": "jpg", "jfif": "jpg"}
    ext = ext_map.get(fmt_lower, fmt_lower)

    orig_name = secure_filename(file_storage.filename or "image")
    base = os.path.splitext(orig_name)[0]
    filename = f"{uuid.uuid4()}_{base}.{ext}"
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)

    if ext in ("jpg", "jpeg"):
        img = img.convert("RGB")
        img.save(filepath, format="JPEG", quality=90)
    else:
        img.save(filepath, format=img.format)

    return filepath


# ===== Parse location =====
def parse_location_to_coords(location_text):
    if not location_text:
        return CITY_COORDS
    parts = [p.strip() for p in location_text.split(",")]
    if len(parts) >= 2:
        try:
            lat = float(parts[0])
            lon = float(parts[1])
            return (lat, lon)
        except Exception:
            pass
    if "muzaffarabad" in location_text.lower() or "azad" in location_text.lower():
        return CITY_COORDS
    return CITY_COORDS


# ===== Routes =====
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")
    location = request.form.get("location", "").strip()
    incharge = request.form.get("incharge", "").strip()

    if not file or file.filename == "":
        return "No file uploaded.", 400

    try:
        filepath = save_uploaded_image(file)
    except ValueError as e:
        return str(e), 400

    # Run model
    detected_set = set()
    if model is not None:
        try:
            results = model(filepath)
            names = getattr(model, "names", {}) or {}
            for res in results:
                if getattr(res, "boxes", None) is not None:
                    for cls in res.boxes.cls:
                        try:
                            detected_set.add(names[int(cls)])
                        except Exception:
                            detected_set.add(str(cls))
        except Exception as e:
            print("Model inference error:", e)
    else:
        detected_set.add("model_missing")

    detected_str = ", ".join(sorted(detected_set)) if detected_set else "None"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(
            """INSERT INTO detections
               (id, filename, detected_classes, timestamp, location, incharge)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (str(uuid.uuid4()), os.path.basename(filepath), detected_str, timestamp, location or None, incharge or None),
        )

    return redirect(url_for("analytics"))


@app.route("/analytics")
def analytics():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, filename, detected_classes, timestamp, location, incharge FROM detections ORDER BY timestamp DESC")
        rows = cursor.fetchall()

    small_count = medium_count = large_count = 0
    map_data = []

    for r in rows:
        detected_field = (r[2] or "").lower()
        if "small" in detected_field:
            small_count += 1
            color = "#28a745"
        elif "medium" in detected_field:
            medium_count += 1
            color = "#ffc107"
        elif "large" in detected_field:
            large_count += 1
            color = "#dc3545"
        else:
            color = "#6c757d"

        coords = parse_location_to_coords(r[4] or "")
        map_data.append({
            "id": r[0],
            "filename": r[1],
            "detected": r[2],
            "timestamp": r[3],
            "location": r[4],
            "incharge": r[5],
            "lat": coords[0],
            "lon": coords[1],
            "color": color
        })

    return render_template("analytics.html",
                           rows=rows,
                           chart_data=[small_count, medium_count, large_count],
                           small_count=small_count,
                           medium_count=medium_count,
                           large_count=large_count,
                           map_data_json=json.dumps(map_data),
                           city_coords=CITY_COORDS,
                           city_name=CITY_NAME)


if __name__ == "__main__":
    app.run(debug=True)
