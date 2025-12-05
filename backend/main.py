from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np
import base64
from ultralytics import YOLO
import json
import asyncio

app = FastAPI()

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load YOLOv8 model
model = YOLO("yolov8n.pt")

@app.get("/")
def read_root():
    return {"message": "YOLOv8 Object Detection API is running"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Receive frame from client
            data = await websocket.receive_text()
            
            # Decode base64 image
            try:
                # Expecting data:image/jpeg;base64,.....
                header, encoded = data.split(",", 1)
                image_data = base64.b64decode(encoded)
                nparr = np.frombuffer(image_data, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                if frame is None:
                    continue

                # Run inference
                results = model(frame, conf=0.4)
                
                detections = []
                for r in results:
                    boxes = r.boxes
                    for box in boxes:
                        # Bounding box coordinates
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        # Confidence
                        conf = float(box.conf[0])
                        # Class name
                        cls = int(box.cls[0])
                        name = model.names[cls]
                        
                        detections.append({
                            "bbox": [x1, y1, x2, y2],
                            "conf": conf,
                            "class": name
                        })

                # Send results back
                await websocket.send_json({"detections": detections})

            except Exception as e:
                print(f"Error processing frame: {e}")
                await websocket.send_json({"error": str(e)})
                
    except WebSocketDisconnect:
        print("Client disconnected")
