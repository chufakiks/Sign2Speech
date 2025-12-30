"""
FastAPI backend for pose conversion and sign language segmentation.

Endpoints:
- GET /api/health - Health check
- POST /api/segment - Convert landmarks and run segmentation
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import logging

from pose_converter import frames_to_pose
from segmentation_service import segment

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Sign2Speech Backend",
    description="Pose conversion and sign language segmentation API",
    version="1.0.0"
)

# CORS configuration for Angular dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=False,  # Must be False when allow_origins is "*"
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
