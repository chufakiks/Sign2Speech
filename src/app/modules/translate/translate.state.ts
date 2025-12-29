import {inject, Injectable} from '@angular/core';
import {Action, NgxsOnInit, State, StateContext, Store} from '@ngxs/store';
import {CopySpokenLanguageText} from './translate.actions';
import {StartCamera} from '../../core/modules/ngxs/store/video/video.actions';
import {Observable} from 'rxjs';
import {EstimatedPose} from '../pose/pose.state';
import {StoreFramePose} from '../pose/pose.actions';
import {PoseService} from '../pose/pose.service';

export interface TranslateStateModel {
  spokenLanguageText: string;
}

const initialState: TranslateStateModel = {
  spokenLanguageText: '',
};

@Injectable()
@State<TranslateStateModel>({
  name: 'translate',
  defaults: initialState,
})
export class TranslateState implements NgxsOnInit {
  private store = inject(Store);
  private poseService = inject(PoseService);

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
  storePose({getState, patchState}: StateContext<TranslateStateModel>, {pose}: StoreFramePose): void {
    const components = ['poseLandmarks', 'faceLandmarks', 'leftHandLandmarks', 'rightHandLandmarks'];
    const normalizedPoseFrame = this.poseService.normalizeHolistic(pose, components);

    // TODO: Process pose for ASL recognition
  }
}
