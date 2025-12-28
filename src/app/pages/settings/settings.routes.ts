import {Routes} from '@angular/router';
import {SettingsPageComponent} from './settings.component';
import {SettingsAppearanceComponent} from './settings-appearance/settings-appearance.component';
import {SettingsOfflineComponent} from './settings-offline/settings-offline.component';
import {SettingsVoiceOutputComponent} from './settings-voice-output/settings-voice-output.component';
import {SettingsVoiceInputComponent} from './settings-voice-input/settings-voice-input.component';

export const routes: Routes = [
  {
    path: '',
    component: SettingsPageComponent,
    children: [
      {path: 'input', component: SettingsVoiceInputComponent},
      {path: 'output', component: SettingsVoiceOutputComponent},
      {path: 'offline', component: SettingsOfflineComponent},
      {path: 'appearance', component: SettingsAppearanceComponent},
      {path: '', redirectTo: 'input', pathMatch: 'full'},
    ],
  },
];
