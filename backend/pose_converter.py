"""
Convert MediaPipe Holistic landmarks from the frontend to pose-format Pose objects.

The frontend sends landmarks as JSON arrays, and we convert them to the binary
pose format expected by the segmentation library.
"""

import numpy as np
from typing import Optional
from pose_format import Pose
from pose_format.numpy import NumPyPoseBody
from pose_format.pose_header import PoseHeader, PoseHeaderDimensions, PoseHeaderComponent
from pose_format.utils.holistic import holistic_components


def create_holistic_header(width: int, height: int, depth: int = 0) -> PoseHeader:
    """
    Create a PoseHeader for MediaPipe Holistic format.

    Uses the official holistic_components() from pose-format library
    to ensure compatibility with downstream tools like segmentation.
    """
    dimensions = PoseHeaderDimensions(width=width, height=height, depth=depth)
    components = holistic_components()

    return PoseHeader(
        version=0.2,
        dimensions=dimensions,
        components=components
    )


def landmarks_to_numpy(
    frames: list[dict],
    width: int,
    height: int
) -> tuple[np.ndarray, np.ndarray]:
    """
    Convert frontend landmark frames to numpy arrays.

    Args:
        frames: List of frame dicts with poseLandmarks, faceLandmarks,
                leftHandLandmarks, rightHandLandmarks
        width: Video width in pixels
        height: Video height in pixels

    Returns:
        data: numpy array of shape (frames, 1, total_points, 3) - XYZ coords
        confidence: numpy array of shape (frames, 1, total_points) - visibility/confidence

    Points layout (543 total for standard holistic):
        - 0-32: POSE_LANDMARKS (33 points)
        - 33-500: FACE_LANDMARKS (468 points)
        - 501-521: LEFT_HAND_LANDMARKS (21 points)
        - 522-542: RIGHT_HAND_LANDMARKS (21 points)
    """
    num_frames = len(frames)

    # Standard MediaPipe Holistic point counts
    POSE_POINTS = 33
    FACE_POINTS = 468
    HAND_POINTS = 21
    TOTAL_POINTS = POSE_POINTS + FACE_POINTS + HAND_POINTS * 2  # 543

    # Initialize arrays with zeros (masked values will remain zero)
    data = np.zeros((num_frames, 1, TOTAL_POINTS, 3), dtype=np.float32)
    confidence = np.zeros((num_frames, 1, TOTAL_POINTS), dtype=np.float32)

    for frame_idx, frame in enumerate(frames):
        point_offset = 0

        # POSE_LANDMARKS (33 points)
        pose_landmarks = frame.get('poseLandmarks') or []
        for i, lm in enumerate(pose_landmarks[:POSE_POINTS]):
            if lm:
                # Landmarks come normalized (0-1), scale to pixel coords
                data[frame_idx, 0, point_offset + i, 0] = lm.get('x', 0) * width
                data[frame_idx, 0, point_offset + i, 1] = lm.get('y', 0) * height
                data[frame_idx, 0, point_offset + i, 2] = lm.get('z', 0) * width  # z scaled by width
                confidence[frame_idx, 0, point_offset + i] = lm.get('visibility', 1.0)
        point_offset += POSE_POINTS

        # FACE_LANDMARKS (468 points)
        face_landmarks = frame.get('faceLandmarks') or []
        for i, lm in enumerate(face_landmarks[:FACE_POINTS]):
            if lm:
                data[frame_idx, 0, point_offset + i, 0] = lm.get('x', 0) * width
                data[frame_idx, 0, point_offset + i, 1] = lm.get('y', 0) * height
                data[frame_idx, 0, point_offset + i, 2] = lm.get('z', 0) * width
                confidence[frame_idx, 0, point_offset + i] = lm.get('visibility', 1.0)
        point_offset += FACE_POINTS

        # LEFT_HAND_LANDMARKS (21 points)
        left_hand = frame.get('leftHandLandmarks') or []
        for i, lm in enumerate(left_hand[:HAND_POINTS]):
            if lm:
                data[frame_idx, 0, point_offset + i, 0] = lm.get('x', 0) * width
                data[frame_idx, 0, point_offset + i, 1] = lm.get('y', 0) * height
                data[frame_idx, 0, point_offset + i, 2] = lm.get('z', 0) * width
                confidence[frame_idx, 0, point_offset + i] = lm.get('visibility', 1.0)
        point_offset += HAND_POINTS

        # RIGHT_HAND_LANDMARKS (21 points)
        right_hand = frame.get('rightHandLandmarks') or []
        for i, lm in enumerate(right_hand[:HAND_POINTS]):
            if lm:
                data[frame_idx, 0, point_offset + i, 0] = lm.get('x', 0) * width
                data[frame_idx, 0, point_offset + i, 1] = lm.get('y', 0) * height
                data[frame_idx, 0, point_offset + i, 2] = lm.get('z', 0) * width
                confidence[frame_idx, 0, point_offset + i] = lm.get('visibility', 1.0)

    return data, confidence


def frames_to_pose(
    frames: list[dict],
    width: int,
    height: int,
    fps: float = 30.0
) -> Pose:
    """
    Convert frontend MediaPipe Holistic frames to a Pose object.

    Args:
        frames: List of frame dicts from frontend
        width: Video width in pixels
        height: Video height in pixels
        fps: Frames per second

    Returns:
        Pose object compatible with pose-format ecosystem
    """
    header = create_holistic_header(width, height)
    data, confidence = landmarks_to_numpy(frames, width, height)

    body = NumPyPoseBody(
        fps=fps,
        data=data,
        confidence=confidence
    )

    return Pose(header=header, body=body)
