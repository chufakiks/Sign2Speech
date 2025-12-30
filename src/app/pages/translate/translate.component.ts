import {Component, inject, OnInit} from '@angular/core';
import {Store} from '@ngxs/store';
import {SetSetting} from '../../modules/settings/settings.actions';
import {fromEvent} from 'rxjs';
import {BaseComponent} from '../../components/base/base.component';
import {takeUntil, tap} from 'rxjs/operators';
import {TranslocoService} from '@jsverse/transloco';
import {Meta, Title} from '@angular/platform-browser';
import {TranslateDesktopComponent} from './translate-desktop/translate-desktop.component';

@Component({
  selector: 'app-translate',
  templateUrl: './translate.component.html',
  styleUrls: ['./translate.component.scss'],
  imports: [TranslateDesktopComponent],
})
export class TranslateComponent extends BaseComponent implements OnInit {
  private store = inject(Store);
  private transloco = inject(TranslocoService);
  private meta = inject(Meta);
  private title = inject(Title);

  constructor() {
    super();

    // Default settings
    this.store.dispatch([
      new SetSetting('receiveVideo', true),
      new SetSetting('detectSign', false),
      new SetSetting('poseViewer', 'pose'),
    ]);
  }

  ngOnInit(): void {
    this.transloco.events$
      .pipe(
        tap(() => {
          this.title.setTitle(this.transloco.translate('translate.title'));
          this.meta.updateTag(
            {
              name: 'description',
              content: this.transloco.translate('translate.description'),
            },
            'name=description'
          );
        }),
        takeUntil(this.ngUnsubscribe)
      )
      .subscribe();

    this.playVideos();
  }

  async playVideos(): Promise<void> {
    if (!('window' in globalThis)) {
      return;
    }

    fromEvent(window, 'click')
      .pipe(
        tap(async () => {
          const videos = Array.from(document.getElementsByTagName('video'));

          for (const video of videos) {
            if (video.autoplay && video.paused) {
              try {
                await video.play();
              } catch (e) {
                console.error(e);
              }
            }
          }
        }),
        takeUntil(this.ngUnsubscribe)
      )
      .subscribe();
  }
}
