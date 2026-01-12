import argparse
import os
import torch
import numpy as np
from PIL import Image
from transformers import AutoImageProcessor, CLIPVisionModel
import cv2

import sys
sys.path.append('./')

from utils.s2wrapper import forward as multiscale_forward

_GLOBAL_SEED = 0
np.random.seed(_GLOBAL_SEED)
torch.manual_seed(_GLOBAL_SEED)


class ViTFeatureReader(object):
    def __init__(
        self, 
        model_name='openai/clip-vit-base-patch32', 
        cache_dir=None,
        device='cuda:0', 
        s2_mode='s2wrapping',
        scales=[1, 2],
        nth_layer=-1
    ):
        self.s2_mode = s2_mode
        self.device = device
        self.scales = scales
        self.nth_layer = nth_layer
        
        self.model = CLIPVisionModel.from_pretrained(
            model_name, output_hidden_states=True, cache_dir=cache_dir
        ).to(device).eval()
        
        self.image_processor = AutoImageProcessor.from_pretrained(model_name)

    @torch.no_grad()
    def forward_features(self, inputs):
        outputs = self.model(inputs).hidden_states
        outputs = outputs[self.nth_layer]
        return outputs

    @torch.no_grad()
    def get_feats(self, video):
        inputs = self.image_processor(list(video), return_tensors="pt").to(self.device).pixel_values
        if self.s2_mode == "s2wrapping":
            outputs = multiscale_forward(self.forward_features, inputs, scales=self.scales, num_prefix_token=1)
        else:
            outputs = self.forward_features(inputs)
        return outputs[:, 0]


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
    parser = argparse.ArgumentParser(description='Extract ViT features from a single video')
    parser.add_argument('--video_path', help='path to input video file', required=True)
    parser.add_argument('--save_path', help='path to save output .npy file', required=True)
    parser.add_argument('--device', help='device to use', default='cuda:0')
    parser.add_argument('--s2_mode', default='s2wrapping', help='s2 mode for multiscale')
    parser.add_argument('--scales', nargs='+', type=int, help='List of scales', default=[1, 2])
    parser.add_argument('--batch_size', type=int, default=32, help='batch size for processing')
    parser.add_argument('--nth_layer', type=int, default=-1, help='which layer to extract features from')
    parser.add_argument('--cache_dir', help='cache dir for model', default=None)
    parser.add_argument('--model_name', help='ViT model name', default='openai/clip-vit-base-patch32')

    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()
    
    # Check if video exists
    if not os.path.exists(args.video_path):
        raise FileNotFoundError(f"Video file not found: {args.video_path}")
    
    print(f"Reading video from: {args.video_path}")
    frames = read_video_frames(args.video_path)
    print(f"Loaded {len(frames)} frames")
    
    if len(frames) == 0:
        raise ValueError("No frames could be read from the video")
    
    # Initialize feature reader
    print("Initializing ViT model...")
    reader = ViTFeatureReader(
        args.model_name, 
        device=args.device, 
        s2_mode=args.s2_mode, 
        scales=args.scales,
        nth_layer=args.nth_layer,
        cache_dir=args.cache_dir
    )
    
    # Extract features in batches
    print("Extracting features...")
    video_feats = []
    for i in range(0, len(frames), args.batch_size):
        batch_end = min(i + args.batch_size, len(frames))
        video_batch = frames[i:batch_end]
        print(f"Processing frames {i} to {batch_end}...")
        
        feats = reader.get_feats(video_batch).cpu().numpy()
        video_feats.append(feats)
    
    # Concatenate all features
    all_feats = np.concatenate(video_feats, axis=0)
    print(f"Feature shape: {all_feats.shape}")
    
    save_dir = os.path.dirname(args.save_path)
    if save_dir:  # Only create directory if there is one
        os.makedirs(save_dir, exist_ok=True)

    # Save features
    np.save(args.save_path, all_feats)
    print(f"Features saved to: {args.save_path}")

if __name__ == "__main__":
    main()