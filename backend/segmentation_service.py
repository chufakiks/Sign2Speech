"""
Wrapper for sign-language-processing/segmentation library.

Provides a simple interface to run sign language segmentation on Pose objects
and return structured results.
"""

from typing import Optional
from pose_format import Pose

# Import the segmentation library
from sign_language_segmentation.bin import segment_pose as _segment_pose


def segment(pose: Pose, fps: float = 30.0) -> dict:
    """
    Run sign language segmentation on a Pose object.

    Args:
        pose: Pose object containing MediaPipe Holistic landmarks
        fps: Frames per second (for calculating time offsets)

    Returns:
        Dictionary with segmentation results:
        {
            "signs": [
                {"start_frame": 0, "end_frame": 15, "start_time": 0.0, "end_time": 0.5},
                ...
            ],
            "sentences": [
                {"start_frame": 0, "end_frame": 45, "start_time": 0.0, "end_time": 1.5},
                ...
            ],
            "frame_count": 90,
            "duration": 3.0
        }
    """
    # Run segmentation
    # Returns (eaf, tiers) where tiers contains "SIGN" and "SENTENCE" lists
    eaf, tiers = _segment_pose(pose, verbose=False)

    # Extract frame count from pose
    frame_count = pose.body.data.shape[0]
    duration = frame_count / fps

    # Convert tiers to structured format
    signs = _extract_segments(tiers.get("SIGN", []), fps)
    sentences = _extract_segments(tiers.get("SENTENCE", []), fps)

    return {
        "signs": signs,
        "sentences": sentences,
        "frame_count": frame_count,
        "duration": duration
    }


def _extract_segments(segments: list, fps: float) -> list[dict]:
    """
    Convert segment tuples to structured dictionaries with time info.

    Args:
        segments: List of segment tuples (start_frame, end_frame) or similar
        fps: Frames per second for time calculation

    Returns:
        List of segment dictionaries with frame and time info
    """
    result = []

    for segment in segments:
        # Segments are dictionaries with 'start' and 'end' keys
        if isinstance(segment, dict) and 'start' in segment and 'end' in segment:
            start_frame = int(segment['start'])
            end_frame = int(segment['end'])
        elif isinstance(segment, (tuple, list)) and len(segment) >= 2:
            start_frame = int(segment[0])
            end_frame = int(segment[1])
        elif hasattr(segment, 'start') and hasattr(segment, 'end'):
            start_frame = int(segment.start)
            end_frame = int(segment.end)
        else:
            # Skip unknown formats
            continue

        result.append({
            "start_frame": start_frame,
            "end_frame": end_frame,
            "start_time": round(start_frame / fps, 3),
            "end_time": round(end_frame / fps, 3)
        })

    return result
