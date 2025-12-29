import {Routes} from '@angular/router';
import {provideStates} from '@ngxs/store';
import {TranslateState} from './modules/translate/translate.state';
import {MainComponent} from './pages/main.component';

export const routes: Routes = [
  {
    path: '',
    component: MainComponent,
    children: [
      {
        path: '',
        loadComponent: () => import('./pages/translate/translate.component').then(m => m.TranslateComponent),
        providers: [provideStates([TranslateState])],
      },
      {
        path: 'translate',
        redirectTo: '',
      },
    ],
  },
  {path: '**', redirectTo: ''},
];
