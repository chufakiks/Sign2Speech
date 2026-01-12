import os
import numpy as np
import torch
import argparse
from PIL import Image
from transformers import VideoMAEModel, VideoMAEImageProcessor
import cv2

import sys
sys.path.append('./')

from utils.helpers import sliding_window_for_list

_GLOBAL_SEED = 0
np.random.seed(_GLOBAL_SEED)
torch.manual_seed(_GLOBAL_SEED)
torch.backends.cudnn.benchmark = True


class VideoMAEFeatureReader(object):
    def __init__(
        self, 
        model_name='MCG-NJU/videomae-base', 
        cache_dir=None,
        device='cuda:0',
        overlap_size=0,
        nth_layer=-1
    ):
        self.device = device
        self.overlap_size = overlap_size
        self.nth_layer = nth_layer

        self.image_processor = VideoMAEImageProcessor.from_pretrained(model_name, cache_dir=cache_dir)
        self.model = VideoMAEModel.from_pretrained(model_name).to(self.device).eval()
        
    @torch.no_grad()
    def get_feats(self, video):
        inputs = self.image_processor(images=video, return_tensors="pt").to(self.device)
        
        outputs = self.model(**inputs, output_hidden_states=True).hidden_states
        
        outputs = outputs[self.nth_layer]
        outputs = outputs[:, 0]
        
        return outputs


def read_video_frames(video_path):
    """Read all frames from a video file"""
    cap = cv2.VideoCapture(video_path)
    frames = []
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Convert to PIL Image
        pil_frame = Image.fromarray(frame_rgb)
        frames.append(pil_frame)
    
    cap.release()
    return frames


def get_parser():
    parser = argparse.ArgumentParser(description='Extract VideoMAE features from a single video')
    parser.add_argument('--video_path', help='path to input video file', required=True)
    parser.add_argument('--save_path', help='path to save output .npy file', required=True)
    parser.add_argument('--model_name', help='VideoMAE model name', default='MCG-NJU/videomae-base')
    parser.add_argument('--batch_size', type=int, default=32, help='batch size for processing')
    parser.add_argument('--device', help='device to use', default='cuda:0')
    parser.add_argument('--overlap_size', type=int, default=8, help='overlap size for sliding window')
    parser.add_argument('--nth_layer', type=int, default=-1, help='which layer to extract features from')
    parser.add_argument('--cache_dir', help='cache dir for model', default=None)
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()
    
    # Check if video exists
    if not os.path.exists(args.video_path):
        raise FileNotFoundError(f"Video file not found: {args.video_path}")
    
    print(f"Reading video from: {args.video_path}")
    image_list = read_video_frames(args.video_path)
    print(f"Loaded {len(image_list)} frames")
    
    if len(image_list) == 0:
        raise ValueError("No frames could be read from the video")
    
    # SAME STEP 1: Pad if less than 16 frames (exactly as original)
    if len(image_list) < 16:
        len_diff = 16 - len(image_list)
        print(f"Padding {len_diff} frames to reach minimum of 16 frames")
        image_list.extend([image_list[-1]] * (16 - len(image_list)))
    
    # SAME STEP 2: Apply sliding window with overlap (exactly as original)
    print(f"Applying sliding window (window_size=16, overlap={args.overlap_size})...")
    image_list_chunks = sliding_window_for_list(image_list, window_size=16, overlap_size=args.overlap_size)
    print(f"Created {len(image_list_chunks)} chunks")
    
    # SAME STEP 3: Convert chunks to video clips (exactly as original)
    videos = []
    for image_chunk in image_list_chunks:
        videos.append(image_chunk)  # Already PIL images
    
    # Initialize feature reader
    print("Initializing VideoMAE model...")
    reader = VideoMAEFeatureReader(
        args.model_name, 
        device=args.device, 
        overlap_size=args.overlap_size, 
        nth_layer=args.nth_layer,
        cache_dir=args.cache_dir
    )
    
    # SAME STEP 4: Extract features in batches (exactly as original)
    print("Extracting features...")
    video_feats = []
    batch_size = args.batch_size
    
    for j in range(0, len(videos), batch_size):
        batch_end = min(j + batch_size, len(videos))
        video_batch = videos[j:batch_end]
        print(f"Processing batch {j//batch_size + 1}/{(len(videos) + batch_size - 1)//batch_size}...")
        
        feats = reader.get_feats(video_batch).cpu().numpy()
        video_feats.append(feats)
    
    # SAME STEP 5: Concatenate all features (exactly as original)
    all_feats = np.concatenate(video_feats, axis=0)
    print(f"Feature shape: {all_feats.shape}")
    
    save_dir = os.path.dirname(args.save_path)
    if save_dir:  # Only create directory if there is one
        os.makedirs(save_dir, exist_ok=True)
    
    # SAME STEP 6: Save with postfix (exactly as original)
    np.save(args.save_path, all_feats)
    print(f"Features saved to: {args.save_path}")


if __name__ == "__main__":
    main()