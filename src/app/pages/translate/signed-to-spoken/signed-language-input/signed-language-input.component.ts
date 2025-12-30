import {Component, inject} from '@angular/core';
import {IonFabButton, IonIcon, IonSpinner, IonSegment, IonSegmentButton, IonLabel} from '@ionic/angular/standalone';
import {addIcons} from 'ionicons';
import {ellipseOutline, stopOutline} from 'ionicons/icons';
import {Store} from '@ngxs/store';
import {AsyncPipe} from '@angular/common';
import {MatTooltipModule} from '@angular/material/tooltip';
import {StartRecording, StopRecording} from '../../../../modules/translate/translate.actions';
import {TranslateStateModel} from '../../../../modules/translate/translate.state';
import {RecordingState} from '../../../../services/recording.service';
import {SetSetting} from '../../../../modules/settings/settings.actions';
import {TranslationModeSetting} from '../../../../modules/settings/settings.state';

@Component({
  selector: 'app-signed-language-input',
  templateUrl: './signed-language-input.component.html',
  styleUrl: './signed-language-input.component.scss',
  imports: [IonFabButton, IonIcon, IonSpinner, IonSegment, IonSegmentButton, IonLabel, AsyncPipe, MatTooltipModule],
})
export class SignedLanguageInputComponent {
  private store = inject(Store);

  recordingState$ = this.store.select<RecordingState>(state => state.translate.recordingState);
  translationMode$ = this.store.select<TranslationModeSetting>(state => state.settings.translationMode);

  constructor() {
    addIcons({ellipseOutline, stopOutline});
  }

  onRecordClick(): void {
    this.store
      .selectOnce<TranslateStateModel>(state => state.translate)
      .subscribe(state => {
        if (state.recordingState === 'idle') {
          this.store.dispatch(new StartRecording());
        } else if (state.recordingState === 'recording') {
          this.store.dispatch(new StopRecording());
        }
      });
  }

  onModeChange(event: CustomEvent): void {
    const mode = event.detail.value as TranslationModeSetting;
    this.store.dispatch(new SetSetting('translationMode', mode));
  }
}
