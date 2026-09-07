# -*- coding: utf-8 -*-
"""Predict emotions on video

Converted from a Jupyter/Colab notebook into a plain Python script.
This script preserves the original tutorial flow but replaces shell magics
and notebook-specific constructs with standard Python.chmod +x setup_env.sh
./setup_env.sh
"""

import os
import sys
import shutil
import urllib.request
import subprocess
import tarfile
import importlib
from typing import List
import argparse
import time
import math

# Helper to ensure a package is importable, installing it via pip if necessary.

def ensure_import(module_name: str, pip_name: str = None):
    """Try to import module_name; if it fails, pip install pip_name (or module_name) and re-import.

    Returns the imported module.
    """
    try:
        return importlib.import_module(module_name)
    except Exception:
        pkg = pip_name or module_name
        print(f"Installing {pkg}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])
        return importlib.import_module(module_name)

# Use ensure_import to import heavy external packages so editor linters don't flag unresolved imports.
try:
    import numpy as np
except Exception:
    np = ensure_import("numpy")

# Function to download test data downloader

def get_test_data_downloader(test_dir: str) -> str:
    input_file = os.path.join(test_dir, "download_test_data.sh")
    if os.path.isfile(input_file):
        return input_file
    url = "https://github.com/sb-ai-lab/EmotiEffLib/blob/main/tests/download_test_data.sh?raw=true"
    print("Downloading download_test_data.sh from", url)
    input_file = "download_test_data.sh"
    if os.path.isfile(input_file):
        return input_file
    urllib.request.urlretrieve(url, input_file)
    return input_file


# Check if running under Colab and install requirements there
try:
    import google.colab  # type: ignore
    IN_COLAB = True
except Exception:
    IN_COLAB = False

if IN_COLAB:
    # In Colab download requirements and install them
    urllib.request.urlretrieve(
        "https://github.com/sb-ai-lab/EmotiEffLib/blob/main/docs/tutorials/python/requirements.txt?raw=true",
        "requirements.txt",
    )
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])


# Prepare test data

data_dir = "data"
if not os.path.exists(data_dir):
    data_downloader = get_test_data_downloader("../../../tests")
    # Remove old data artifacts if present
    if os.path.exists("data"):
        shutil.rmtree("data")
    if os.path.exists("data.tar.gz"):
        os.remove("data.tar.gz")
    # Run the downloader script (it will produce data.tar.gz)
    subprocess.check_call(["sh", data_downloader])
    # Extract data.tar.gz
    if os.path.exists("data.tar.gz"):
        with tarfile.open("data.tar.gz", "r:gz") as tar:
            tar.extractall()
else:
    print("Data directory already exists. Skipping download and extraction.")


# Function for faces recognition
from typing import List as _List

# Note: facenet_pytorch is imported later to allow on-demand installation

def recognize_faces(frame: np.ndarray, device: str) -> _List[np.ndarray]:
    """
    Detects faces in the given image and returns the facial images cropped from the original.

    Args:
        frame (numpy.ndarray): The image frame in which faces need to be detected.
        device (str): The device to run the MTCNN face detection model on, e.g., 'cpu' or 'cuda'.

    Returns:
        list: A list of numpy arrays, representing a cropped face image from the original image.
    """

    # Import MTCNN lazily to allow the script to install requirements first if needed
    facenet_pytorch = ensure_import("facenet_pytorch")
    MTCNN = facenet_pytorch.MTCNN

    def detect_face(frame: np.ndarray):
        mtcnn = MTCNN(keep_all=False, post_process=False, min_face_size=40, device=device)
        bounding_boxes, probs = mtcnn.detect(frame, landmarks=False)
        if probs is None or len(probs) == 0 or probs[0] is None:
            return []
        bounding_boxes = bounding_boxes[probs > 0.9]
        return bounding_boxes

    bounding_boxes = detect_face(frame)
    facial_images: _List[np.ndarray] = []
    for bbox in bounding_boxes:
        box = bbox.astype(int)
        x1, y1, x2, y2 = box[0:4]
        facial_images.append(frame[y1:y2, x1:x2, :])
    return facial_images


# Ensure EmotiEffLib is available (install on demand)
# We'll attempt to import the required symbols and install emotiefflib if missing.
_emotiefflib = None
try:
    from emotiefflib.facial_analysis import EmotiEffLibRecognizer, get_model_list  # type: ignore
except Exception:
    ensure_import("emotiefflib")
    from emotiefflib.facial_analysis import EmotiEffLibRecognizer, get_model_list  # type: ignore


# Import other visualization libraries
try:
    import cv2
except Exception:
    cv2 = ensure_import("opencv-python", "opencv-python")

try:
    import matplotlib.pyplot as plt
except Exception:
    matplotlib = ensure_import("matplotlib")
    plt = matplotlib.pyplot


def run_example(
    engine: str = "onnx",
    device: str = "cpu",
    use_webcam: bool = False,
    duration: float = None,
):
    """Run the recognize-emotions-on-video example for a given engine and device.

    If use_webcam is True, use webcam as input.
    If duration is provided (seconds), webcam capture stops automatically after that time.
    """
    test_dir = "data"
    model_name = get_model_list()[0]

    if use_webcam:
        print("Using webcam for real-time emotion recognition. Press 'q' to quit.")
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Error: Could not open webcam.")
            return
        start_time = time.monotonic()
        if duration is not None and duration <= 0:
            print("Duration must be > 0 seconds. Ignoring duration.")
            duration = None
    else:
        input_file = os.path.join(test_dir, "video_samples", "emotions", "Angry", "Angry.mp4")
        cap = cv2.VideoCapture(input_file)

    fer = EmotiEffLibRecognizer(engine=engine, model_name=model_name, device=device)
    all_scores = None
    snapshots = []
    snapshot_interval_sec = 0.5  # 2 snapshots per second
    next_snapshot_time = 0.0

    processing_start = time.monotonic()

    def current_stream_time_sec() -> float:
        if use_webcam:
            return time.monotonic() - processing_start
        pos_msec = cap.get(cv2.CAP_PROP_POS_MSEC)
        if pos_msec is not None and pos_msec > 0:
            return pos_msec / 1000.0
        return time.monotonic() - processing_start

    while cap.isOpened():
        success, image = cap.read()
        if not success:
            break
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        facial_images = recognize_faces(image_rgb, device)
        if len(facial_images) == 0:
            if use_webcam:
                cv2.imshow('Webcam', image)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            continue
        emotions, scores = fer.predict_emotions(facial_images, logits=True)

        elapsed_sec = current_stream_time_sec()
        if elapsed_sec >= next_snapshot_time:
            snapshots.append((facial_images[0].copy(), elapsed_sec, emotions[0]))
            while elapsed_sec >= next_snapshot_time:
                next_snapshot_time += snapshot_interval_sec

        if all_scores is not None:
            all_scores = np.concatenate((all_scores, scores))
        else:
            all_scores = scores
        if use_webcam:
            # Show webcam with emotion label
            cv2.putText(image, f"Emotion: {emotions[0]}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
            cv2.imshow('Webcam', image)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            if duration is not None and (time.monotonic() - start_time) >= duration:
                print(f"Reached webcam duration limit: {duration} seconds")
                break
    cap.release()
    if use_webcam:
        cv2.destroyAllWindows()
    if all_scores is not None:
        score = np.mean(all_scores, axis=0)
        emotion_idx = np.argmax(score)
        print(f"Most likely emotion (mean over frames): {fer.idx_to_emotion_class[emotion_idx]}")

    # Build one final image file containing all captured snapshots with time labels.
    if len(snapshots) == 0:
        fig = plt.figure(figsize=(8, 3))
        plt.text(0.5, 0.5, "No face snapshots captured", ha="center", va="center", fontsize=14)
        plt.axis("off")
    else:
        n = len(snapshots)
        cols = 4
        rows = math.ceil(n / cols)
        fig, axes = plt.subplots(rows, cols, figsize=(4 * cols, 3 * rows))
        axes_array = np.array(axes).reshape(-1)

        for idx, (face_img, ts, emotion_name) in enumerate(snapshots):
            axes_array[idx].imshow(face_img)
            axes_array[idx].set_title(f"{ts:.1f}s | {emotion_name}")
            axes_array[idx].axis("off")

        for idx in range(n, len(axes_array)):
            axes_array[idx].axis("off")

        plt.tight_layout()

    plt.savefig("emotion_results.png")
    plt.show()


def main():
    parser = argparse.ArgumentParser(description="Emotion recognition on video or webcam.")
    parser.add_argument('--webcam', action='store_true', help='Use webcam as input instead of video file')
    parser.add_argument(
        '--duration',
        type=float,
        default=None,
        help='Webcam capture duration in seconds (only used with --webcam)',
    )
    args = parser.parse_args()
    if args.duration is not None and not args.webcam:
        print("--duration is only used with --webcam. Ignoring it for file input.")

    try:
        print("Running emotion recognition...")
        run_example(engine="onnx", device="cpu", use_webcam=args.webcam, duration=args.duration)
    except Exception as e:
        print("Emotion recognition failed:", e)


if __name__ == "__main__":
    main()