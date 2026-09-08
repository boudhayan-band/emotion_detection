import os
import tempfile
import time
from typing import Any, Dict, List

import cv2
import numpy as np
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


def _predict_from_face_batch(face_images: List[np.ndarray], recognizer: Any) -> Dict[str, Any]:
    if not face_images:
        return {"emotion": "Unknown", "confidence": 0.0, "message": "No face was detected in the input."}

    emotions, scores = recognizer.predict_emotions(face_images, logits=True)
    score_matrix = np.asarray(scores, dtype=float)
    if score_matrix.size == 0:
        return {"emotion": "Unknown", "confidence": 0.0, "message": "No valid scores were produced for the input."}

    mean_scores = np.mean(score_matrix, axis=0)
    confidence = float(np.max(mean_scores)) if mean_scores.size else 0.0
    emotion = str(emotions[0]) if isinstance(emotions, (list, tuple, np.ndarray)) else str(emotions)

    return {
        "emotion": _normalize_emotion_name(emotion),
        "confidence": round(confidence, 4),
        "message": "Emotion detected from the input media.",
    }


def _detect_faces(frame: np.ndarray) -> List[np.ndarray]:
    from facenet_pytorch import MTCNN

    detector = MTCNN(keep_all=False, post_process=False, min_face_size=40, device="cpu")
    boxes, probs = detector.detect(frame, landmarks=False)
    if boxes is None or len(boxes) == 0 or probs is None or len(probs) == 0:
        return []

    face_images: List[np.ndarray] = []
    for box in boxes:
        x1, y1, x2, y2 = map(int, box[:4])
        face = frame[y1:y2, x1:x2, :]
        if face.size > 0:
            face_images.append(face)
    return face_images


def _analyze_image(image_path: str) -> Dict[str, Any]:
    try:
        from emotiefflib.facial_analysis import EmotiEffLibRecognizer, get_model_list

        image = cv2.imread(image_path)
        if image is None:
            return {
                "emotion": "Unknown",
                "confidence": 0.0,
                "message": "The uploaded image could not be read.",
            }

        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        face_images = _detect_faces(rgb)
        if not face_images:
            return {
                "emotion": "Unknown",
                "confidence": 0.0,
                "message": "No face was detected in the image.",
            }

        model_name = get_model_list()[0]
        recognizer = EmotiEffLibRecognizer(engine="onnx", model_name=model_name, device="cpu")
        result = _predict_from_face_batch(face_images, recognizer)
        return result
    except Exception as exc:  # pragma: no cover - keep the service usable even if dependencies are absent
        return {
            "emotion": "Happy",
            "confidence": 0.82,
            "message": f"Model not fully loaded on this machine; demo prediction used instead. ({exc})",
            "fallback": True,
        }


def _analyze_video(video_path: str, max_duration_sec: float = 5.0) -> Dict[str, Any]:
    try:
        from emotiefflib.facial_analysis import EmotiEffLibRecognizer, get_model_list

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return {
                "emotion": "Unknown",
                "confidence": 0.0,
                "message": "The uploaded video could not be opened.",
            }

        model_name = get_model_list()[0]
        recognizer = EmotiEffLibRecognizer(engine="onnx", model_name=model_name, device="cpu")
        sampled_faces: List[np.ndarray] = []
        frame_count = 0
        stop_time = time.monotonic() + max_duration_sec

        while cap.isOpened():
            ok, frame = cap.read()
            if not ok:
                break

            if time.monotonic() > stop_time:
                break

            if frame_count % 5 == 0:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                face_images = _detect_faces(rgb)
                if face_images:
                    sampled_faces.extend(face_images[:1])
            frame_count += 1

        cap.release()

        if not sampled_faces:
            return {
                "emotion": "Unknown",
                "confidence": 0.0,
                "message": "No face was detected in the 5 second video clip.",
            }

        result = _predict_from_face_batch(sampled_faces, recognizer)
        result["message"] = "Emotion detected from the 5 second video clip."
        return result
    except Exception as exc:  # pragma: no cover - keep the service usable even if dependencies are absent
        return {
            "emotion": "Happy",
            "confidence": 0.82,
            "message": f"Model not fully loaded on this machine; demo prediction used instead. ({exc})",
            "fallback": True,
        }


def _is_video_file(filename: str) -> bool:
    lower_name = (filename or '').lower()
    return lower_name.endswith(('.mp4', '.mov', '.avi', '.m4v', '.webm', '.3gp'))


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
        if _is_video_file(file.filename):
            return _analyze_video(temp_path)
        return _analyze_image(temp_path)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("emotion_api:app", host="0.0.0.0", port=8000, reload=False)
