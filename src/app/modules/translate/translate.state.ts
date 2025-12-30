import {inject, Injectable} from '@angular/core';
import {Action, NgxsOnInit, State, StateContext, Store} from '@ngxs/store';
import {CopySpokenLanguageText, StartRecording, StopRecording, CancelRecording} from './translate.actions';
import {StartCamera} from '../../core/modules/ngxs/store/video/video.actions';
import {Observable} from 'rxjs';
import {EstimatedPose} from '../pose/pose.state';
import {StoreFramePose} from '../pose/pose.actions';
import {RecordingService, RecordingState, SegmentationResult} from '../../services/recording.service';

export interface TranslateStateModel {
  spokenLanguageText: string;
  recordingState: RecordingState;
  segmentationResult: SegmentationResult | null;
  recordingError: string | null;
}

const initialState: TranslateStateModel = {
  spokenLanguageText: '',
  recordingState: 'idle',
  segmentationResult: null,
  recordingError: null,
};

@Injectable()
@State<TranslateStateModel>({
  name: 'translate',
  defaults: initialState,
})
export class TranslateState implements NgxsOnInit {
  private store = inject(Store);
  private recordingService = inject(RecordingService);

  pose$!: Observable<EstimatedPose>;

  constructor() {
    this.pose$ = this.store.select<EstimatedPose>(state => state.pose.pose);
  }

  ngxsOnInit(context: StateContext<TranslateStateModel>): void {
    context.dispatch(StartCamera);
  }

  @Action(CopySpokenLanguageText)
  async copySpokenLanguageText({getState}: StateContext<TranslateStateModel>): Promise<void> {
    const {spokenLanguageText} = getState();

    try {
      await navigator.clipboard.writeText(spokenLanguageText);
    } catch (e) {
      console.error(e);
      alert(e.message);
    }
  }

  @Action(StoreFramePose)
  storePose(_ctx: StateContext<TranslateStateModel>, {pose}: StoreFramePose): void {
    // If recording, add frame to the recording buffer
    if (this.recordingService.isRecording) {
      this.recordingService.addFrame(pose);
    }
  }

  @Action(StartRecording)
  startRecording({patchState}: StateContext<TranslateStateModel>): void {
    this.recordingService.startRecording();
    patchState({
      recordingState: 'recording',
      segmentationResult: null,
      recordingError: null,
    });
  }

  @Action(StopRecording)
  async stopRecording({patchState}: StateContext<TranslateStateModel>): Promise<void> {
    patchState({recordingState: 'processing'});

    const result = await this.recordingService.stopRecording();

    if (result) {
      patchState({
        recordingState: 'idle',
        segmentationResult: result,
        recordingError: null,
      });
    } else {
      patchState({
        recordingState: 'idle',
        recordingError: 'Segmentation failed or recording too short',
      });
    }
  }

  @Action(CancelRecording)
  cancelRecording({patchState}: StateContext<TranslateStateModel>): void {
    this.recordingService.cancelRecording();
    patchState({
      recordingState: 'idle',
      segmentationResult: null,
      recordingError: null,
    });
  }
}
