# Sign2Speech Backend

Python FastAPI backend for pose conversion and sign language segmentation.

## Features

- Converts MediaPipe Holistic landmarks to `.pose` format
- Runs sign language segmentation using [sign-language-processing/segmentation](https://github.com/sign-language-processing/segmentation)
- Returns sign and sentence boundaries with timestamps

## Requirements

- Python 3.10+
- ~2GB disk space for models (downloaded on first run)

## Installation

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

## Running the Server

```bash
# Development mode with auto-reload
uvicorn main:app --reload --port 8000

# Or run directly
python main.py
```

The server will be available at `http://localhost:8000`.

## API Endpoints

### Health Check

```
GET /api/health
```

Returns:

```json
{"status": "ok", "service": "sign2speech-backend"}
```

### Segmentation

```
POST /api/segment
Content-Type: application/json
```

Request body:

```json
{
  "frames": [
    {
      "poseLandmarks": [{"x": 0.5, "y": 0.3, "z": 0.1, "visibility": 0.9}, ...],
      "faceLandmarks": [{"x": 0.5, "y": 0.3, "z": 0.1}, ...],
      "leftHandLandmarks": [{"x": 0.5, "y": 0.3, "z": 0.1}, ...],
      "rightHandLandmarks": [{"x": 0.5, "y": 0.3, "z": 0.1}, ...]
    }
  ],
  "width": 1280,
  "height": 720,
  "fps": 30.0
}
```

Response:

```json
{
  "signs": [
    {"start_frame": 0, "end_frame": 15, "start_time": 0.0, "end_time": 0.5},
    {"start_frame": 16, "end_frame": 45, "start_time": 0.53, "end_time": 1.5}
  ],
  "sentences": [{"start_frame": 0, "end_frame": 45, "start_time": 0.0, "end_time": 1.5}],
  "frame_count": 90,
  "duration": 3.0
}
```

## API Documentation

Once the server is running, interactive API docs are available at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Notes

- First request may be slow as the segmentation model is downloaded (~100MB)
- Minimum 10 frames required for segmentation
- Recommended: 30+ frames for meaningful results
- Landmarks should be normalized (0-1 range) as provided by MediaPipe
