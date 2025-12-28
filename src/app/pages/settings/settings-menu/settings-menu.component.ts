import {Component} from '@angular/core';
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
  groups: PagesGroup[] = [];
}
