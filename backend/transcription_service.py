"""
Pose to SignWriting transcription service.

Wraps the signwriting-transcription library to convert pose data
with sign segments into SignWriting notation.
"""

import tempfile
import os
from pathlib import Path
from pose_format import Pose
import pympi


def transcribe_pose_to_signwriting(pose: Pose, eaf_path: str) -> list[dict]:
    """
    Transcribe pose segments to SignWriting notation.

    Args:
        pose: Pose object containing the pose data
        eaf_path: Path to ELAN file with sign segment annotations

    Returns:
        List of dicts with segment info and SignWriting:
        [
            {
                "start_frame": 57,
                "end_frame": 110,
                "signwriting": "M500x500S33100482x483..."
            },
            ...
        ]
    """
    # Import here to avoid loading heavy dependencies at module level
    from signwriting_transcription.pose_to_signwriting.bin import (
        download_model,
        preprocessing_signs,
        translate,
        create_test_config,
        build_pose_vocab,
        pose_to_matrix,
    )
    from signwriting_transcription.pose_to_signwriting.joeynmt_pose.prediction import predict

    # Download/load the model
    experiment_dir = Path(os.getcwd()) / "experiment"
    model_name = "bc2de71.ckpt"
    download_model(experiment_dir, model_name)

    # Load ELAN file to get sign annotations
    eaf = pympi.Elan.Eaf(file_path=eaf_path)

    # Get sign tier annotations
    sign_tier = eaf.get_annotation_data_for_tier("SIGN")
    if not sign_tier:
        return []

    # Preprocess signs and get SignWriting predictions
    # This follows the same logic as the bin.py main() function
    results = []

    # Build pose vocabulary and config
    pose_vocab = build_pose_vocab(pose)

    # Create test config
    config = create_test_config(experiment_dir, pose_vocab)

    # Preprocess pose data for each sign segment
    preprocessed = preprocessing_signs(pose, sign_tier, strategy="tight")

    if not preprocessed:
        return []

    # Get predictions
    predictions = predict(config, preprocessed)

    # Combine with segment info
    for i, (start_ms, end_ms, _) in enumerate(sign_tier):
        if i < len(predictions):
            # Convert ms to frames (assuming 30fps default)
            fps = pose.body.fps if hasattr(pose.body, 'fps') else 30
            start_frame = int(start_ms / 1000 * fps)
            end_frame = int(end_ms / 1000 * fps)

            results.append({
                "start_frame": start_frame,
                "end_frame": end_frame,
                "start_time": start_ms / 1000,
                "end_time": end_ms / 1000,
                "signwriting": predictions[i]
            })

    return results


def transcribe_pose_simple(pose_path: str, eaf_path: str) -> list[str]:
    """
    Simple interface to transcribe pose file to SignWriting.

    Args:
        pose_path: Path to .pose file
        eaf_path: Path to .eaf file with segments

    Returns:
        List of SignWriting strings for each sign segment
    """
    # Use the CLI-style approach which is more reliable
    from signwriting_transcription.pose_to_signwriting.bin import main
    import sys

    # Capture the output
    old_argv = sys.argv
    sys.argv = ['bin.py', '--pose', pose_path, '--elan', eaf_path]

    try:
        main()
    finally:
        sys.argv = old_argv

    # Read back the updated ELAN file to get SignWriting annotations
    eaf = pympi.Elan.Eaf(file_path=eaf_path)

    # The transcription adds SignWriting to the SIGN tier values
    sign_tier = eaf.get_annotation_data_for_tier("SIGN")

    return [annotation[2] for annotation in sign_tier if annotation[2]]
