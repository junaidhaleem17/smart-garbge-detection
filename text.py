
from ultralytics import YOLO

# Load YOLO model
model = YOLO("best.pt")

results = model.predict('C:\\garbage-detection\\uploads\\test.mov', save=True)
