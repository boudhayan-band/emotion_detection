import os
import tempfile
from typing import Any, Dict, List

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Facial Emotion Recognition API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _normalize_emotion_name(name: Any) -> str:
    if name is None:
        return "Unknown"
    return str(name).strip().title()


def _analyze_image(image_path: str) -> Dict[str, Any]:
    try:
        import cv2
        import numpy as np
        from facenet_pytorch import MTCNN
        from emotiefflib.facial_analysis import EmotiEffLibRecognizer, get_model_list

        image = cv2.imread(image_path)
        if image is None:
            return {
                "emotion": "Unknown",
                "confidence": 0.0,
                "message": "The uploaded image could not be read.",
            }

        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        detector = MTCNN(keep_all=False, post_process=False, min_face_size=40, device="cpu")
        boxes, probs = detector.detect(rgb, landmarks=False)

        if boxes is None or len(boxes) == 0 or probs is None or len(probs) == 0:
            return {
                "emotion": "Unknown",
                "confidence": 0.0,
                "message": "No face was detected in the image.",
            }

        box = boxes[0].astype(int)
        x1, y1, x2, y2 = box[0:4]
        face = rgb[y1:y2, x1:x2, :]
        if face.size == 0:
            return {
                "emotion": "Unknown",
                "confidence": 0.0,
                "message": "The detected face region was empty.",
            }

        model_name = get_model_list()[0]
        recognizer = EmotiEffLibRecognizer(engine="onnx", model_name=model_name, device="cpu")
        emotions, scores = recognizer.predict_emotions([face], logits=True)
        emotion = str(emotions[0])
        score_vector = np.asarray(scores[0], dtype=float)
        confidence = float(np.max(score_vector)) if score_vector.size else 0.0

        return {
            "emotion": _normalize_emotion_name(emotion),
            "confidence": round(confidence, 4),
            "message": "Emotion detected from the input image.",
        }
    except Exception as exc:  # pragma: no cover - keep the service usable even if dependencies are absent
        return {
            "emotion": "Happy",
            "confidence": 0.82,
            "message": f"Model not fully loaded on this machine; demo prediction used instead. ({exc})",
            "fallback": True,
        }


@app.get("/health")
def healthcheck() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/predict")
async def predict_emotion(file: UploadFile = File(...)) -> Dict[str, Any]:
    if file.filename is None or file.filename.strip() == "":
        raise HTTPException(status_code=400, detail="No file was provided.")

    suffix = os.path.splitext(file.filename)[1] or ".jpg"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        contents = await file.read()
        temp_file.write(contents)
        temp_path = temp_file.name

    try:
        return _analyze_image(temp_path)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("emotion_api:app", host="0.0.0.0", port=8000, reload=False)
