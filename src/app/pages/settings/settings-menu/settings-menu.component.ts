import {Component} from '@angular/core';
import {SettingsOfflineComponent} from '../settings-offline/settings-offline.component';
import {SettingsVoiceInputComponent} from '../settings-voice-input/settings-voice-input.component';
import {SettingsVoiceOutputComponent} from '../settings-voice-output/settings-voice-output.component';
import {SettingsAppearanceComponent} from '../settings-appearance/settings-appearance.component';
import {TranslocoDirective} from '@jsverse/transloco';
import {
  IonContent,
  IonHeader,
  IonIcon,
  IonItem,
  IonLabel,
  IonList,
  IonListHeader,
  IonNavLink,
  IonTitle,
  IonToolbar,
} from '@ionic/angular/standalone';
import {addIcons} from 'ionicons';
import {airplane, mic, personCircle, volumeMedium} from 'ionicons/icons';

interface Page {
  path: string;
  icon: string;
  component: any;
}

interface PagesGroup {
  name: string;
  pages: Page[];
}

@Component({
  selector: 'app-settings-menu',
  templateUrl: './settings-menu.component.html',
  styleUrls: ['./settings-menu.component.scss'],
  imports: [
    TranslocoDirective,
    IonHeader,
    IonToolbar,
    IonTitle,
    IonContent,
    IonList,
    IonListHeader,
    IonLabel,
    IonNavLink,
    IonItem,
    IonIcon,
  ],
})
export class SettingsMenuComponent {
  groups: PagesGroup[] = [
    {
      name: 'voice',
      pages: [
        {path: 'input', icon: 'mic', component: SettingsVoiceInputComponent},
        {path: 'output', icon: 'volume-medium', component: SettingsVoiceOutputComponent},
      ],
    },
    {
      name: 'other',
      pages: [
        {path: 'offline', icon: 'airplane', component: SettingsOfflineComponent},
        {path: 'appearance', icon: 'person-circle', component: SettingsAppearanceComponent},
      ],
    },
  ];

  constructor() {
    addIcons({mic, volumeMedium, airplane, personCircle});
  }
}
