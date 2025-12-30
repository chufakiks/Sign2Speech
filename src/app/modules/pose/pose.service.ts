import {inject, Injectable} from '@angular/core';
import {EMPTY_LANDMARK, EstimatedPose, PoseLandmark} from './pose.state';
import {MediapipeHolisticService} from '../../core/services/holistic.service';

@Injectable({
  providedIn: 'root',
})
export class PoseService {
  private holistic = inject(MediapipeHolisticService);

  model?: any;

  // loadPromise must be static, in case multiple PoseService instances are created (during testing)
  static loadPromise: Promise<any>;

  isFirstFrame = true;
  onResultsCallbacks = [];

  onResults(onResultsCallback) {
    this.onResultsCallbacks.push(onResultsCallback);
  }

  async load(): Promise<void> {
    if (!PoseService.loadPromise) {
      PoseService.loadPromise = this._load();
    }

    // Holistic loading may fail for various reasons.
    // If that fails, show an alert to the user, for further investigation.
    try {
      await PoseService.loadPromise;
    } catch (e) {
      console.error(e);
      alert(e.message);
    }
  }

  private async _load(): Promise<void> {
    if (this.model) {
      return;
    }

    await this.holistic.load();

    this.model = new this.holistic.Holistic({locateFile: file => `assets/models/holistic/${file}`});

    this.model.setOptions({
      upperBodyOnly: false,
      modelComplexity: 1,
    });

    await this.model.initialize();

    // Send an empty frame, to force the mediapipe computation graph to load
    const frame = document.createElement('canvas');
    frame.width = 256;
    frame.height = 256;
    await this.model.send({image: frame});
    frame.remove();

    // Track following results
    this.model.onResults(results => {
      for (const callback of this.onResultsCallbacks) {
        callback(results);
      }
    });
  }

  async predict(video: HTMLVideoElement | HTMLImageElement): Promise<void> {
    await this.load();
    this.isFirstFrame = false;
    await this.model.send({image: video});
  }

  normalizeHolistic(pose: EstimatedPose, components: string[], normalized = true): PoseLandmark[] {
    // This calculation takes up to 0.05ms for 543 landmarks
    const vectors = {
      poseLandmarks: pose.poseLandmarks || new Array(33).fill(EMPTY_LANDMARK),
      faceLandmarks: pose.faceLandmarks || new Array(468).fill(EMPTY_LANDMARK),
      leftHandLandmarks: pose.leftHandLandmarks || new Array(21).fill(EMPTY_LANDMARK),
      rightHandLandmarks: pose.rightHandLandmarks || new Array(21).fill(EMPTY_LANDMARK),
    };
    let landmarks = components.reduce((acc, component) => acc.concat(vectors[component]), []);

    // Scale by image dimensions
    landmarks = landmarks.map(l => ({
      x: l.x * pose.image.width,
      y: l.y * pose.image.height,
      z: l.z * pose.image.width,
    }));

    if (normalized && pose.poseLandmarks) {
      const p1 = landmarks[this.holistic.POSE_LANDMARKS.LEFT_SHOULDER];
      const p2 = landmarks[this.holistic.POSE_LANDMARKS.RIGHT_SHOULDER];
      const scale = Math.sqrt((p2.x - p1.x) ** 2 + (p2.y - p1.y) ** 2 + (p2.z - p1.z) ** 2);

      const dx = (p1.x + p2.x) / 2;
      const dy = (p1.y + p2.y) / 2;
      const dz = (p1.z + p2.z) / 2;

      // Normalize all non-zero landmarks
      landmarks = landmarks.map(l => ({
        x: l.x === 0 ? 0 : (l.x - dx) / scale,
        y: l.y === 0 ? 0 : (l.y - dy) / scale,
        z: l.z === 0 ? 0 : (l.z - dz) / scale,
      }));
    }

    return landmarks;
  }
}
