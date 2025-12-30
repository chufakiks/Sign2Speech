import {inject, Injectable} from '@angular/core';
import {HttpClient} from '@angular/common/http';
import {BehaviorSubject, Observable, firstValueFrom} from 'rxjs';
import {EstimatedPose, PoseLandmark} from '../modules/pose/pose.state';
import {environment} from '../../environments/environment';

export interface SegmentBoundary {
  start_frame: number;
  end_frame: number;
  start_time: number;
  end_time: number;
}

export interface TranslatedSign {
  start_frame: number;
  end_frame: number;
  start_time: number;
  end_time: number;
  signwriting: string;
  text: string;
}

export interface TranslationResult {
  signs: TranslatedSign[];
  sentences: SegmentBoundary[];
  full_text: string;
  frame_count: number;
  duration: number;
}

// Keep old interface for backward compatibility
export interface SegmentationResult {
  signs: SegmentBoundary[];
  sentences: SegmentBoundary[];
  frame_count: number;
  duration: number;
}

export type RecordingState = 'idle' | 'recording' | 'processing';

interface LandmarkPayload {
  x: number;
  y: number;
  z: number;
  visibility?: number;
}

interface FramePayload {
  poseLandmarks: LandmarkPayload[] | null;
  faceLandmarks: LandmarkPayload[] | null;
  leftHandLandmarks: LandmarkPayload[] | null;
  rightHandLandmarks: LandmarkPayload[] | null;
}

interface SegmentRequest {
  frames: FramePayload[];
  width: number;
  height: number;
  fps: number;
}

@Injectable({
  providedIn: 'root',
})
export class RecordingService {
  private http = inject(HttpClient);

  private frames: EstimatedPose[] = [];
  private recordingState$ = new BehaviorSubject<RecordingState>('idle');
  private translationResult$ = new BehaviorSubject<TranslationResult | null>(null);
  private error$ = new BehaviorSubject<string | null>(null);

  private recordingStartTime = 0;
  private fps = 30;

  get state$(): Observable<RecordingState> {
    return this.recordingState$.asObservable();
  }

  get result$(): Observable<TranslationResult | null> {
    return this.translationResult$.asObservable();
  }

  get error(): Observable<string | null> {
    return this.error$.asObservable();
  }

  get frameCount(): number {
    return this.frames.length;
  }

  get isRecording(): boolean {
    return this.recordingState$.value === 'recording';
  }

  get isProcessing(): boolean {
    return this.recordingState$.value === 'processing';
  }

  startRecording(): void {
    if (this.recordingState$.value !== 'idle') {
      return;
    }

    this.frames = [];
    this.translationResult$.next(null);
    this.error$.next(null);
    this.recordingStartTime = Date.now();
    this.recordingState$.next('recording');
  }

  addFrame(pose: EstimatedPose): void {
    if (this.recordingState$.value !== 'recording') {
      return;
    }

    this.frames.push(pose);
  }

  async stopRecording(): Promise<TranslationResult | null> {
    if (this.recordingState$.value !== 'recording') {
      return null;
    }

    const recordingDuration = (Date.now() - this.recordingStartTime) / 1000;
    this.fps = this.frames.length / recordingDuration;

    if (this.frames.length < 10) {
      this.error$.next('Recording too short. Need at least 10 frames.');
      this.recordingState$.next('idle');
      return null;
    }

    this.recordingState$.next('processing');

    try {
      const result = await this.sendForTranslation();
      this.translationResult$.next(result);
      this.recordingState$.next('idle');
      return result;
    } catch (e) {
      const errorMessage = e instanceof Error ? e.message : 'Translation failed';
      this.error$.next(errorMessage);
      this.recordingState$.next('idle');
      return null;
    }
  }

  cancelRecording(): void {
    this.frames = [];
    this.recordingState$.next('idle');
    this.error$.next(null);
  }

  private async sendForTranslation(): Promise<TranslationResult> {
    const payload = this.buildPayload();
    const backendUrl = environment.backendUrl || 'http://localhost:8000';

    console.log(`📤 Sending ${payload.frames.length} frames to ${backendUrl}/api/translate`);
    const result = await firstValueFrom(this.http.post<TranslationResult>(`${backendUrl}/api/translate`, payload));

    console.log('📥 Translation result:');
    console.log(`   Signs: ${result.signs.length}`);
    result.signs.forEach((sign, i) => {
      console.log(`   ${i + 1}. "${sign.text}" (${sign.start_time}s - ${sign.end_time}s)`);
      console.log(`      SignWriting: ${sign.signwriting}`);
    });
    console.log(`   Full text: "${result.full_text}"`);

    return result;
  }

  private buildPayload(): SegmentRequest {
    // Get dimensions from first frame's image
    const firstFrame = this.frames[0];
    const width = firstFrame?.image?.width || 1280;
    const height = firstFrame?.image?.height || 720;

    const frames: FramePayload[] = this.frames.map(pose => ({
      poseLandmarks: this.convertLandmarks(pose.poseLandmarks),
      faceLandmarks: this.convertLandmarks(pose.faceLandmarks),
      leftHandLandmarks: this.convertLandmarks(pose.leftHandLandmarks),
      rightHandLandmarks: this.convertLandmarks(pose.rightHandLandmarks),
    }));

    return {
      frames,
      width,
      height,
      fps: this.fps,
    };
  }

  private convertLandmarks(landmarks: PoseLandmark[] | null): LandmarkPayload[] | null {
    if (!landmarks || landmarks.length === 0) {
      return null;
    }

    return landmarks.map(lm => ({
      x: lm.x,
      y: lm.y,
      z: lm.z,
      visibility: lm.visibility,
    }));
  }
}
