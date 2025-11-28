# 🗑️ Smart Garbage Detection & Classification using YOLOv11
A Flask-based web application that detects and classifies garbage (Small, Medium, Large) using a fine-tuned YOLOv11 model. The system stores detection results in a local SQLite database and visualizes detections with analytics and geolocation mapping.

---

## 🎯 Project Overview
This project automates garbage detection in urban environments using computer vision.  
Users can upload images, and the system:

- Runs detection using a custom-trained **YOLOv11** model (`best.pt`)
- Classifies trash into **Small, Medium, and Large**
- Stores each detection in a **SQLite database**
- Saves uploaded images locally
- Displays analytical dashboards including:
  - Count of each trash type
  - List of detections with timestamps
  - Map visualization (using fixed or user-entered location)

This makes the system suitable for:
- Smart city applications  
- Waste management monitoring  
- Environmental cleanliness analysis  

---

## 📂 Project Structure

project/
│── app.py # Main Flask application
│── best.pt # YOLOv11 trained model (not included in repo)
│── database.db # SQLite DB (auto-created)
│── templates/
│ ├── index.html
│ ├── analytics.html
│── uploads/ # User-uploaded images
│── runs/ # YOLO detection outputs (optional)
│── static/ # CSS/JS/Assets (if any)
│── README.md
│── .gitignore


---

## 🚀 Features

### ✔ Garbage Detection  
Detects **small, medium, and large** trash using YOLOv11.

### ✔ Secure File Upload  
Validates & processes images safely using Pillow.

### ✔ Location Tagging  
If no location is entered, defaults to:  
**Muzaffarabad, Azad Kashmir (34.3700, 73.4711)**

### ✔ SQLite Database Logging  
Stores:
- File name  
- Detected classes  
- Timestamp  
- Location  
- Incharge / employee name  

### ✔ Analytical Dashboard  
Includes:
- Trash quantity chart  
- Detection table  
- Map with geo-points  

---

## 🧠 Tech Stack

| Component | Technology |
|----------|------------|
| Backend | Flask (Python) |
| Detection Model | YOLOv11 (Ultralytics) |
| Database | SQLite |
| Frontend | HTML, CSS, JS, Leaflet Maps |
| Image Processing | Pillow |

---

## 🔧 Installation & Setup

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/yourusername/smart-garbage-detection.git
cd smart-garbage-detection
