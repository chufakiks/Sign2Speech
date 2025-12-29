import {Component, inject} from '@angular/core';
import {Store} from '@ngxs/store';
import {CopySpokenLanguageText} from '../../../modules/translate/translate.actions';
import {Observable} from 'rxjs';
import {MatTooltipModule} from '@angular/material/tooltip';
import {IonButton, IonIcon} from '@ionic/angular/standalone';
import {TextToSpeechComponent} from '../../../components/text-to-speech/text-to-speech.component';
import {addIcons} from 'ionicons';
import {copyOutline} from 'ionicons/icons';
import {TranslocoPipe} from '@jsverse/transloco';
import {AsyncPipe} from '@angular/common';
import {VideoModule} from '../../../components/video/video.module';

@Component({
  selector: 'app-signed-to-spoken',
  templateUrl: './signed-to-spoken.component.html',
  styleUrls: ['./signed-to-spoken.component.scss'],
  imports: [MatTooltipModule, IonButton, TextToSpeechComponent, VideoModule, IonIcon, TranslocoPipe, AsyncPipe],
})
export class SignedToSpokenComponent {
  private store = inject(Store);

  spokenLanguageText$: Observable<string>;

  constructor() {
    this.spokenLanguageText$ = this.store.select<string>(state => state.translate.spokenLanguageText);
    addIcons({copyOutline});
  }

  copyTranslation() {
    this.store.dispatch(CopySpokenLanguageText);
  }
}
