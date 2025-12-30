import {Component, inject} from '@angular/core';
import {IonFabButton, IonIcon, IonSpinner} from '@ionic/angular/standalone';
import {addIcons} from 'ionicons';
import {ellipseOutline, stopOutline} from 'ionicons/icons';
import {Store} from '@ngxs/store';
import {AsyncPipe} from '@angular/common';
import {MatTooltipModule} from '@angular/material/tooltip';
import {StartRecording, StopRecording} from '../../../../modules/translate/translate.actions';
import {TranslateStateModel} from '../../../../modules/translate/translate.state';
import {RecordingState} from '../../../../services/recording.service';

@Component({
  selector: 'app-signed-language-input',
  templateUrl: './signed-language-input.component.html',
  styleUrl: './signed-language-input.component.scss',
  imports: [IonFabButton, IonIcon, IonSpinner, AsyncPipe, MatTooltipModule],
})
export class SignedLanguageInputComponent {
  private store = inject(Store);

  recordingState$ = this.store.select<RecordingState>(state => state.translate.recordingState);

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
}
