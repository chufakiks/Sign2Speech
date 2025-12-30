import {Component, inject, OnInit} from '@angular/core';
import {Store} from '@ngxs/store';
import {BaseComponent} from '../../../components/base/base.component';
import {IonContent, IonHeader, IonTitle, IonToolbar} from '@ionic/angular/standalone';
import {SignedToSpokenComponent} from '../signed-to-spoken/signed-to-spoken.component';
import {StartCamera} from '../../../core/modules/ngxs/store/video/video.actions';

@Component({
  selector: 'app-translate-desktop',
  templateUrl: './translate-desktop.component.html',
  styleUrls: ['./translate-desktop.component.scss'],
  imports: [IonContent, IonHeader, IonTitle, IonToolbar, SignedToSpokenComponent],
})
export class TranslateDesktopComponent extends BaseComponent implements OnInit {
  private store = inject(Store);

  constructor() {
    super();
  }

  ngOnInit(): void {
    this.store.dispatch(StartCamera);
  }
}
