"""
FastAPI backend for pose conversion, segmentation, and translation.

Endpoints:
- GET /api/health - Health check
- POST /api/segment - Convert landmarks and run segmentation
- POST /api/translate - Full pipeline: segment, transcribe, translate to text
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import logging
import tempfile
import os

from pose_converter import frames_to_pose
from segmentation_service import segment
from translation_service import translate_signs

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Sign2Speech Backend",
    description="Pose conversion and sign language segmentation API",
    version="1.0.0"
)

# CORS configuration for Angular dev server
# Allow localhost and common local network ranges for development
allowed_origins = [
    "http://localhost:4200",
    "http://localhost:4000",
    "http://127.0.0.1:4200",
    "http://127.0.0.1:4000",
]

# Allow local network IPs (192.168.x.x) for development
# In production, replace this with specific allowed domains
import re
def is_local_network(origin: str) -> bool:
    return bool(re.match(r"^http://(192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}):\d+$", origin))

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1|192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}):\d+$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for request/response
class Landmark(BaseModel):
    x: float
    y: float
    z: float
    visibility: Optional[float] = 1.0


class PoseFrame(BaseModel):
    poseLandmarks: Optional[list[Landmark]] = None
    faceLandmarks: Optional[list[Landmark]] = None
    leftHandLandmarks: Optional[list[Landmark]] = None
    rightHandLandmarks: Optional[list[Landmark]] = None


class SegmentRequest(BaseModel):
    frames: list[PoseFrame]
    width: int
    height: int
    fps: float = 30.0


class SegmentBoundary(BaseModel):
    start_frame: int
    end_frame: int
    start_time: float
    end_time: float


class SegmentResponse(BaseModel):
    signs: list[SegmentBoundary]
    sentences: list[SegmentBoundary]
    frame_count: int
    duration: float


class TranslateRequest(BaseModel):
    frames: list[PoseFrame]
    width: int
    height: int
    fps: float = 30.0
    target_language: str = "en"


class TranslatedSign(BaseModel):
    start_frame: int
    end_frame: int
    start_time: float
    end_time: float
    signwriting: str
    text: str


class TranslateResponse(BaseModel):
    signs: list[TranslatedSign]
    sentences: list[SegmentBoundary]
    full_text: str
    frame_count: int
    duration: float


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "sign2speech-backend"}


@app.post("/api/segment", response_model=SegmentResponse)
async def segment_endpoint(request: SegmentRequest):
    """
    Convert MediaPipe Holistic landmarks to pose format and run segmentation.

    Returns sign and sentence boundaries detected in the pose sequence.
    """
    if not request.frames:
        raise HTTPException(status_code=400, detail="No frames provided")

    if len(request.frames) < 10:
        raise HTTPException(
            status_code=400,
            detail=f"Too few frames ({len(request.frames)}). Need at least 10 frames for segmentation."
        )

    logger.info(f"Received segmentation request: {len(request.frames)} frames, {request.width}x{request.height}, {request.fps}fps")

    try:
        # Convert frames to list of dicts for pose_converter
        frames_data = []
        for frame in request.frames:
            frame_dict = {
                'poseLandmarks': [lm.model_dump() for lm in frame.poseLandmarks] if frame.poseLandmarks else None,
                'faceLandmarks': [lm.model_dump() for lm in frame.faceLandmarks] if frame.faceLandmarks else None,
                'leftHandLandmarks': [lm.model_dump() for lm in frame.leftHandLandmarks] if frame.leftHandLandmarks else None,
                'rightHandLandmarks': [lm.model_dump() for lm in frame.rightHandLandmarks] if frame.rightHandLandmarks else None,
            }
            frames_data.append(frame_dict)

        # Convert to Pose object
        pose = frames_to_pose(
            frames=frames_data,
            width=request.width,
            height=request.height,
            fps=request.fps
        )

        logger.info(f"Created Pose object with shape: {pose.body.data.shape}")

        # Run segmentation
        result = segment(pose, fps=request.fps)

        logger.info(f"Segmentation complete: {len(result['signs'])} signs, {len(result['sentences'])} sentences")

        return SegmentResponse(**result)

    except Exception as e:
        logger.error(f"Segmentation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Segmentation failed: {str(e)}")


@app.post("/api/translate", response_model=TranslateResponse)
async def translate_endpoint(request: TranslateRequest):
    """
    Full translation pipeline: segment poses, transcribe to SignWriting, translate to text.

    Returns sign boundaries with SignWriting notation and English text translation.
    """
    if not request.frames:
        raise HTTPException(status_code=400, detail="No frames provided")

    if len(request.frames) < 10:
        raise HTTPException(
            status_code=400,
            detail=f"Too few frames ({len(request.frames)}). Need at least 10 frames for translation."
        )

    logger.info(f"Received translation request: {len(request.frames)} frames, {request.width}x{request.height}, {request.fps}fps")

    try:
        # Convert frames to list of dicts for pose_converter
        frames_data = []
        for frame in request.frames:
            frame_dict = {
                'poseLandmarks': [lm.model_dump() for lm in frame.poseLandmarks] if frame.poseLandmarks else None,
                'faceLandmarks': [lm.model_dump() for lm in frame.faceLandmarks] if frame.faceLandmarks else None,
                'leftHandLandmarks': [lm.model_dump() for lm in frame.leftHandLandmarks] if frame.leftHandLandmarks else None,
                'rightHandLandmarks': [lm.model_dump() for lm in frame.rightHandLandmarks] if frame.rightHandLandmarks else None,
            }
            frames_data.append(frame_dict)

        # Convert to Pose object
        pose = frames_to_pose(
            frames=frames_data,
            width=request.width,
            height=request.height,
            fps=request.fps
        )

        logger.info(f"Created Pose object with shape: {pose.body.data.shape}")

        # Step 1: Run segmentation
        from sign_language_segmentation.bin import segment_pose
        eaf, tiers = segment_pose(pose, verbose=False)

        frame_count = pose.body.data.shape[0]
        duration = frame_count / request.fps

        # Extract segments
        sign_segments = tiers.get("SIGN", [])
        sentence_segments = tiers.get("SENTENCE", [])

        if not sign_segments:
            logger.info("No signs detected in pose data")
            return TranslateResponse(
                signs=[],
                sentences=[],
                full_text="",
                frame_count=frame_count,
                duration=duration
            )

        logger.info(f"Segmentation complete: {len(sign_segments)} signs, {len(sentence_segments)} sentences")

        # Step 2: Transcribe to SignWriting
        # Use the library functions directly instead of CLI to avoid file I/O issues
        from pathlib import Path
        from pose_format.utils.generic import reduce_holistic
        from signwriting_transcription.pose_to_signwriting.bin import (
            download_model, preprocessing_signs
        )
        from signwriting_transcription.pose_to_signwriting.joeynmt_pose.prediction import translate as sw_translate

        # Prepare experiment directory and download model
        experiment_dir = Path('experiment')
        experiment_dir.mkdir(exist_ok=True)
        download_model(experiment_dir, 'bc2de71.ckpt')

        # Preprocess the pose (reduce holistic without normalization)
        preprocessed_pose = reduce_holistic(pose)

        # Get sign annotations from our segmentation (convert to ms format)
        sign_annotations = []
        for seg in sign_segments:
            start_ms = int(seg['start'] / request.fps * 1000)
            end_ms = int(seg['end'] / request.fps * 1000)
            sign_annotations.append((start_ms, end_ms, ""))

        logger.info(f"Prepared {len(sign_annotations)} sign annotations for transcription")

        # Run transcription
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_files = preprocessing_signs(preprocessed_pose, sign_annotations, 'tight', temp_dir)
            signwriting_list = sw_translate('experiment/config.yaml', temp_files)

        logger.info(f"Transcribed {len(signwriting_list)} signs to SignWriting: {signwriting_list}")

        # Step 3: Translate SignWriting to text
        if signwriting_list:
            translations = translate_signs(signwriting_list, request.target_language)
        else:
            translations = []

        logger.info(f"Translated to: {translations}")

        # Build response
        translated_signs = []
        for i, seg in enumerate(sign_segments):
            start_frame = seg['start']
            end_frame = seg['end']
            sw = signwriting_list[i] if i < len(signwriting_list) else ""
            text = translations[i] if i < len(translations) else ""

            translated_signs.append(TranslatedSign(
                start_frame=start_frame,
                end_frame=end_frame,
                start_time=round(start_frame / request.fps, 3),
                end_time=round(end_frame / request.fps, 3),
                signwriting=sw,
                text=text
            ))

        # Build sentence boundaries
        sentences = []
        for seg in sentence_segments:
            sentences.append(SegmentBoundary(
                start_frame=seg['start'],
                end_frame=seg['end'],
                start_time=round(seg['start'] / request.fps, 3),
                end_time=round(seg['end'] / request.fps, 3)
            ))

        # Combine all translations into full text
        full_text = " ".join(translations)

        return TranslateResponse(
            signs=translated_signs,
            sentences=sentences,
            full_text=full_text,
            frame_count=frame_count,
            duration=duration
        )

    except Exception as e:
        logger.error(f"Translation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
