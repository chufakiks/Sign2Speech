"""
SpaMo Sign Language Translation Service.

This module provides functions to:
1. Extract spatial features from video frames using CLIP ViT
2. Extract motion features from video frames using VideoMAE
3. Run translation inference using the SpaMo model
"""

import os
import sys
import torch
import numpy as np
from PIL import Image
from typing import List, Dict, Optional, Tuple
import logging

# Add spamo paths
SPAMO_DIR = os.path.join(os.path.dirname(__file__), 'spamo')
SPAMO_MODEL_DIR = os.path.join(SPAMO_DIR, 'model_code')
sys.path.insert(0, SPAMO_DIR)
sys.path.insert(0, SPAMO_MODEL_DIR)

logger = logging.getLogger(__name__)

# Global model cache
_vit_reader = None
_mae_reader = None
_spamo_model = None
_device = 'cpu'


def get_device():
    """Get the best available device."""
    if torch.cuda.is_available():
        return 'cuda:0'
    return 'cpu'


def sliding_window_for_list(data_list: List, window_size: int, overlap_size: int) -> List[List]:
    """Apply a sliding window to a list."""
    step_size = window_size - overlap_size
    windows = [
        data_list[i:i + window_size]
        for i in range(0, len(data_list), step_size)
        if i + window_size <= len(data_list)
    ]
    return windows


class ViTFeatureExtractor:
    """Extract spatial features using CLIP ViT model."""

    def __init__(
        self,
        model_name: str = 'openai/clip-vit-large-patch14',
        device: str = 'cpu',
        scales: List[int] = [1, 2],
        nth_layer: int = -1
    ):
        from transformers import AutoImageProcessor, CLIPVisionModel
        from utils.s2wrapper import forward as multiscale_forward

        self.device = device
        self.scales = scales
        self.nth_layer = nth_layer
        self.multiscale_forward = multiscale_forward

        logger.info(f"Loading CLIP ViT model: {model_name}")
        self.model = CLIPVisionModel.from_pretrained(
            model_name, output_hidden_states=True
        ).to(device).eval()

        self.image_processor = AutoImageProcessor.from_pretrained(model_name)
        logger.info("CLIP ViT model loaded")

    @torch.no_grad()
    def forward_features(self, inputs):
        outputs = self.model(inputs).hidden_states
        outputs = outputs[self.nth_layer]
        return outputs

    @torch.no_grad()
    def get_feats(self, frames: List[Image.Image], batch_size: int = 32) -> np.ndarray:
        """Extract features from a list of PIL Image frames."""
        all_feats = []

        for i in range(0, len(frames), batch_size):
            batch = frames[i:i + batch_size]
            inputs = self.image_processor(list(batch), return_tensors="pt").to(self.device).pixel_values

            # Use multiscale forward for s2wrapping
            outputs = self.multiscale_forward(
                self.forward_features,
                inputs,
                scales=self.scales,
                num_prefix_token=1
            )

            # Extract CLS token
            feats = outputs[:, 0].cpu().numpy()
            all_feats.append(feats)

        return np.concatenate(all_feats, axis=0)


class VideoMAEFeatureExtractor:
    """Extract motion features using VideoMAE model."""

    def __init__(
        self,
        model_name: str = 'MCG-NJU/videomae-large',
        device: str = 'cpu',
        overlap_size: int = 8,
        nth_layer: int = -1
    ):
        from transformers import VideoMAEModel, VideoMAEImageProcessor

        self.device = device
        self.overlap_size = overlap_size
        self.nth_layer = nth_layer

        logger.info(f"Loading VideoMAE model: {model_name}")
        self.image_processor = VideoMAEImageProcessor.from_pretrained(model_name)
        self.model = VideoMAEModel.from_pretrained(model_name).to(device).eval()
        logger.info("VideoMAE model loaded")

    @torch.no_grad()
    def get_feats(self, frames: List[Image.Image], batch_size: int = 32) -> np.ndarray:
        """Extract motion features from frames using sliding window."""
        # Pad if less than 16 frames
        if len(frames) < 16:
            frames = frames + [frames[-1]] * (16 - len(frames))

        # Apply sliding window (window_size=16, overlap=8)
        chunks = sliding_window_for_list(frames, window_size=16, overlap_size=self.overlap_size)

        if not chunks:
            # If video is too short even after padding, use single chunk
            chunks = [frames[:16]]

        all_feats = []

        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i:i + batch_size]
            inputs = self.image_processor(images=batch_chunks, return_tensors="pt").to(self.device)

            outputs = self.model(**inputs, output_hidden_states=True).hidden_states
            outputs = outputs[self.nth_layer]

            # Extract CLS token (first position)
            feats = outputs[:, 0].cpu().numpy()
            all_feats.append(feats)

        return np.concatenate(all_feats, axis=0)


class SpaMoTranslator:
    """SpaMo sign language to text translation model."""

    def __init__(
        self,
        config_path: str,
        checkpoint_path: str,
        device: str = 'cpu'
    ):
        from omegaconf import OmegaConf
        from utils.helpers import instantiate_from_config

        self.device = device

        logger.info(f"Loading SpaMo config from: {config_path}")
        config = OmegaConf.load(config_path)

        # Override cache_dir to avoid permission issues
        if 'params' in config.model:
            config.model.params.cache_dir = None

        logger.info("Instantiating SpaMo model...")
        self.model = instantiate_from_config(config.model)

        logger.info(f"Loading checkpoint from: {checkpoint_path}")
        state = torch.load(checkpoint_path, map_location=device)
        self.model.load_state_dict(state["state_dict"], strict=False)

        self.model = self.model.to(device).eval()
        logger.info("SpaMo model loaded and ready")

    @torch.no_grad()
    def translate(
        self,
        spatial_features: np.ndarray,
        motion_features: np.ndarray,
        target_language: str = "German"
    ) -> str:
        """Translate sign language features to text."""
        # Convert to tensors
        spatial = torch.from_numpy(spatial_features).float().to(self.device)
        motion = torch.from_numpy(motion_features).float().to(self.device)

        # Prepare input dict matching the expected format
        # Based on the model's prepare_visual_inputs method
        samples = {
            'pixel_values': [spatial],  # List of tensors
            'glor_values': [motion],     # List of tensors
            'num_frames': [len(spatial)],
            'glor_lengths': [len(motion)],
            'text': [''],  # Empty for inference
            'lang': [target_language],
            'ex_lang_trans': [''],
        }

        # Prepare visual inputs
        visual_outputs, visual_masks = self.model.prepare_visual_inputs(samples)
        visual_outputs = self.model.fusion_proj(visual_outputs)

        # Prepare prompt
        bs = visual_outputs.shape[0]
        prompts = [f'{self.model.prompt}'] * bs
        prompts = [p.format(l) for p, l in zip(prompts, samples['lang'])]

        # Tokenize prompts
        input_tokens = self.model.t5_tokenizer(
            prompts,
            padding="longest",
            truncation=True,
            return_tensors="pt",
        ).to(self.device)

        # Get lengths
        visual_lengths = visual_masks.sum(1)
        prompt_lengths = input_tokens.attention_mask.sum(1)
        new_lengths = visual_lengths + prompt_lengths

        # Convert tokens to embeddings
        input_embeds = self.model.t5_model.encoder.embed_tokens(input_tokens.input_ids)

        # Concatenate visual and text embeddings
        from torch.nn.utils.rnn import pad_sequence
        from utils.helpers import create_mask

        joint_outputs = []
        for i in range(bs):
            vis_out = visual_outputs[i, :visual_lengths[i], :]
            prompt_embeds = input_embeds[i, :prompt_lengths[i], :]
            concat_sample = torch.cat((vis_out, prompt_embeds), dim=0)
            joint_outputs.append(concat_sample)

        joint_outputs = pad_sequence(joint_outputs, batch_first=True)
        joint_mask = create_mask(seq_lengths=new_lengths.tolist(), device=self.device)

        # Generate translation
        generated = self.model.t5_model.generate(
            inputs_embeds=joint_outputs,
            attention_mask=joint_mask,
            num_beams=5,
            max_length=self.model.max_txt_len,
            top_p=0.9,
            do_sample=True,
        )

        # Decode
        translation = self.model.t5_tokenizer.batch_decode(generated, skip_special_tokens=True)
        return translation[0].lower()


def get_vit_extractor() -> ViTFeatureExtractor:
    """Get or create the ViT feature extractor (singleton)."""
    global _vit_reader
    if _vit_reader is None:
        _vit_reader = ViTFeatureExtractor(device=get_device())
    return _vit_reader


def get_mae_extractor() -> VideoMAEFeatureExtractor:
    """Get or create the VideoMAE feature extractor (singleton)."""
    global _mae_reader
    if _mae_reader is None:
        _mae_reader = VideoMAEFeatureExtractor(device=get_device())
    return _mae_reader


def get_spamo_model() -> SpaMoTranslator:
    """Get or create the SpaMo model (singleton)."""
    global _spamo_model
    if _spamo_model is None:
        config_path = os.path.join(SPAMO_DIR, 'finetune.yaml')
        checkpoint_path = os.path.join(SPAMO_DIR, 'spamo.ckpt')
        _spamo_model = SpaMoTranslator(
            config_path=config_path,
            checkpoint_path=checkpoint_path,
            device=get_device()
        )
    return _spamo_model


def translate_frames(frames: List[Image.Image], target_language: str = "German") -> Dict:
    """
    Full translation pipeline: extract features and translate.

    Args:
        frames: List of PIL Image frames
        target_language: Target language for translation (German for Phoenix14T)

    Returns:
        Dict with translation result and metadata
    """
    if len(frames) < 10:
        return {
            'translation': '',
            'error': 'Too few frames for translation',
            'frame_count': len(frames)
        }

    logger.info(f"Translating {len(frames)} frames to {target_language}")

    # Extract spatial features
    logger.info("Extracting spatial features...")
    vit_extractor = get_vit_extractor()
    spatial_features = vit_extractor.get_feats(frames)
    logger.info(f"Spatial features shape: {spatial_features.shape}")

    # Extract motion features
    logger.info("Extracting motion features...")
    mae_extractor = get_mae_extractor()
    motion_features = mae_extractor.get_feats(frames)
    logger.info(f"Motion features shape: {motion_features.shape}")

    # Translate
    logger.info("Running translation...")
    model = get_spamo_model()
    translation = model.translate(spatial_features, motion_features, target_language)
    logger.info(f"Translation: {translation}")

    return {
        'translation': translation,
        'spatial_features_shape': list(spatial_features.shape),
        'motion_features_shape': list(motion_features.shape),
        'frame_count': len(frames),
        'target_language': target_language
    }
