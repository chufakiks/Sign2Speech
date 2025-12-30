import {Injectable} from '@angular/core';
import {Action, State, StateContext} from '@ngxs/store';
import {SetSetting} from './settings.actions';

export type PoseViewerSetting = 'pose' | 'person';
export type TranslationModeSetting = 'signwriting' | 'spamo';

export interface SettingsStateModel {
  receiveVideo: boolean;

  detectSign: boolean;

  drawVideo: boolean;
  drawSignWriting: boolean;

  appearance: string;

  poseViewer: PoseViewerSetting;
  translationMode: TranslationModeSetting;
}

const initialState: SettingsStateModel = {
  receiveVideo: false,

  detectSign: false,

  drawVideo: true,
  drawSignWriting: false,

  poseViewer: 'pose',
  translationMode: 'signwriting',

  appearance: '#ffffff',
};

@Injectable()
@State<SettingsStateModel>({
  name: 'settings',
  defaults: initialState,
})
export class SettingsState {
  @Action(SetSetting)
  setSetting({patchState}: StateContext<SettingsStateModel>, {setting, value}: SetSetting): void {
    patchState({[setting]: value});
  }
}
