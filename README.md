# Facial Emotion Recognition (Simple Guide)

This project predicts **facial emotion** from either:
- a sample video file (default), or
- your webcam (`--webcam`)

You do **not** need to be an ML expert to run it.

---

## What this script does

Main script: `predict_emotions_on_video.py`

In simple words, it does this:
1. Checks/install required Python packages if missing.
2. Checks if test data exists in `data/`; downloads it if missing.
3. Opens input source:
   - sample video file, or
   - webcam.
4. For each frame:
   - detects face(s),
   - crops face image,
   - predicts emotion scores.
5. Every 0.5 seconds (2 times per second), grabs a face snapshot.
6. Labels each snapshot with capture time (for example `3.5s`) and predicted emotion.
7. Aggregates scores across frames.
8. Prints the most likely emotion.
9. Saves a **single collage image** as `emotion_results.png`.

---

## Setup (one time)

From project folder:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

If `data/` does not exist, the script usually downloads test data automatically.

---

## How to run

### 1) Use default sample video

```bash
python predict_emotions_on_video.py
```

### 2) Use webcam

```bash
python predict_emotions_on_video.py --webcam
```

### 3) Use webcam for fixed seconds

```bash
python predict_emotions_on_video.py --webcam --duration 10
```

This stops webcam capture automatically after 10 seconds.

---

## Script sequence (Flow Diagram)

```mermaid
flowchart TD
    A[Start Script] --> B[Load/Install Dependencies]
    B --> C{data/ exists?}
    C -- No --> D[Download + Extract test data]
    C -- Yes --> E[Skip data download]
    D --> F[Choose input source]
    E --> F

    F --> G{--webcam flag?}
    G -- Yes --> H[Open webcam]
    G -- No --> I[Open sample video file]

    H --> J[Read next frame]
    I --> J

    J --> K{Frame available?}
    K -- No --> Q[Finish loop]
    K -- Yes --> L[Detect face(s)]

    L --> M{Any face found?}
    M -- No --> N[Continue to next frame]
    M -- Yes --> O[Crop face + Predict emotion]

    O --> P[Store emotion scores]
    P --> P2{Snapshot time reached? (every 0.5s)}
    P2 -- Yes --> P3[Save snapshot + time label]
    P2 -- No --> R
    P3 --> R
    R{Webcam duration reached or q pressed?}
    R -- Yes --> Q
    R -- No --> J
    N --> J

    Q --> S[Compute mean score across frames]
    S --> T[Print most likely emotion]
    T --> U[Create single collage image emotion_results.png]
    U --> V[End]
```

---

## Output you should expect

- Terminal output:
  - status logs,
  - final line like: `Most likely emotion (mean over frames): ...`
- File output:
  - `emotion_results.png` (single collage image with snapshots captured at 2/sec, each labeled with time + predicted emotion)

---

## Common issues

- **Webcam does not open**
  - Close other apps using camera.
  - Give camera permission to terminal/IDE.

- **Slow performance**
  - Webcam mode can be slower on CPU.
  - Reduce other heavy apps while running.

- **No face detected**
  - Ensure face is visible and well-lit.
  - Move closer to camera.

---

## Quick command summary

```bash
# activate env
source .venv/bin/activate

# run on sample video
python predict_emotions_on_video.py

# run on webcam for 10 seconds
python predict_emotions_on_video.py --webcam --duration 10
```

---

## Mobile app demo

A mobile app has been added under `mobile_app/` that lets a user pick or capture a face image and send it to a Python API for emotion prediction.

### Start the backend locally

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn emotion_api:app --host 0.0.0.0 --port 8000
```

### Start the Expo app locally

```bash
cd mobile_app
npm install
npm start
```

Then run the app in an emulator/simulator or browser. For Android emulators, use `http://10.0.2.2:8000`; for iPhone simulators use `http://127.0.0.1:8000`.

---

## Deploy backend to the cloud

The app cannot use `localhost` in a real iPhone build or TestFlight install. The backend must be hosted on a public URL.

### Option 1: Deploy on Render

1. Push the repo to GitHub.
2. Go to https://render.com and create a new Web Service.
3. Connect the GitHub repo.
4. Set:
   - Root directory: `backend`
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn emotion_api:app --host 0.0.0.0 --port $PORT`
5. Deploy.
6. Confirm the health endpoint:

```bash
https://<your-render-service>.onrender.com/health
```

### Set the mobile app to the public backend URL

Create a `.env` file in `mobile_app/`:

```bash
EXPO_PUBLIC_API_URL=https://<your-render-service>.onrender.com
```

Then restart the Expo app.

For the production build, EAS will read this environment variable automatically.

---

## Build and distribute to iPhone via TestFlight

1. Install EAS CLI:

```bash
npm install -g eas-cli
```

2. Log in:

```bash
eas login
```

3. Configure the app:

```bash
cd mobile_app
eas build:configure
```

4. Create an iOS build:

```bash
eas build --platform ios
```

5. Upload the build to App Store Connect and submit it to TestFlight.
6. Invite testers or add your own Apple ID as a tester.

This is the normal path for installing the app like a regular iPhone app.
