import {Component, inject} from '@angular/core';
import {Store} from '@ngxs/store';
import {CopySpokenLanguageText} from '../../../modules/translate/translate.actions';
import {Observable} from 'rxjs';
import {MatTooltipModule} from '@angular/material/tooltip';
import {IonButton, IonIcon, IonSegment, IonSegmentButton, IonLabel} from '@ionic/angular/standalone';
import {TextToSpeechComponent} from '../../../components/text-to-speech/text-to-speech.component';
import {addIcons} from 'ionicons';
import {copyOutline} from 'ionicons/icons';
import {TranslocoPipe} from '@jsverse/transloco';
import {AsyncPipe} from '@angular/common';
import {VideoModule} from '../../../components/video/video.module';
import {SignedLanguageInputComponent} from './signed-language-input/signed-language-input.component';
import {SetSetting} from '../../../modules/settings/settings.actions';
import {TranslationModeSetting} from '../../../modules/settings/settings.state';

@Component({
  selector: 'app-signed-to-spoken',
  templateUrl: './signed-to-spoken.component.html',
  styleUrls: ['./signed-to-spoken.component.scss'],
  imports: [
    MatTooltipModule,
    IonButton,
    TextToSpeechComponent,
    VideoModule,
    IonIcon,
    IonSegment,
    IonSegmentButton,
    IonLabel,
    TranslocoPipe,
    AsyncPipe,
    SignedLanguageInputComponent,
  ],
})
export class SignedToSpokenComponent {
  private store = inject(Store);

  spokenLanguageText$: Observable<string>;
  translationMode$ = this.store.select<TranslationModeSetting>(state => state.settings.translationMode);

  constructor() {
    this.spokenLanguageText$ = this.store.select<string>(state => state.translate.spokenLanguageText);
    addIcons({copyOutline});
  }

  copyTranslation() {
    this.store.dispatch(CopySpokenLanguageText);
  }

  onModeChange(event: CustomEvent): void {
    const mode = event.detail.value as TranslationModeSetting;
    this.store.dispatch(new SetSetting('translationMode', mode));
  }
}
