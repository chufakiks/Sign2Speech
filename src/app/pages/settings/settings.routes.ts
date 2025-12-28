import {Routes} from '@angular/router';
import {SettingsPageComponent} from './settings.component';

export const routes: Routes = [
  {
    path: '',
    component: SettingsPageComponent,
    children: [],
  },
];
