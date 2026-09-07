# Emotion recognition backend

This service exposes a small FastAPI API that accepts an image upload and returns the predicted emotion.

## Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn emotion_api:app --host 0.0.0.0 --port 8000
```

## Mobile app config

Use the following URL from the mobile app:

- Android emulator: `http://10.0.2.2:8000/predict`
- iOS simulator: `http://127.0.0.1:8000/predict`
- Physical device: replace `127.0.0.1` with your computer IP address

## Test

```bash
curl -X POST http://127.0.0.1:8000/predict -F "file=@/path/to/face.jpg"
```
