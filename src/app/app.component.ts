import {Component, inject} from '@angular/core';
import {TranslocoService} from '@jsverse/transloco';
import {tap} from 'rxjs/operators';
import {languageCodeNormalizer} from './core/modules/transloco/languages';
import {IonApp, IonRouterOutlet} from '@ionic/angular/standalone';
import {MediaMatcher} from '@angular/cdk/layout';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss'],
  imports: [IonApp, IonRouterOutlet],
})
export class AppComponent {
  private transloco = inject(TranslocoService);
  private mediaMatcher = inject(MediaMatcher);

  constructor() {
    this.listenLanguageChange();
    this.updateToolbarColor();
  }

  updateToolbarColor() {
    if (!('window' in globalThis)) {
      return;
    }

    const matcher = this.mediaMatcher.matchMedia('(prefers-color-scheme: dark)');

    function onColorSchemeChange(): any {
      const toolbar = document.querySelector('ion-toolbar');
      if (!toolbar) {
        return requestAnimationFrame(onColorSchemeChange);
      }

      const toolbarColor = window.getComputedStyle(toolbar).getPropertyValue('--background');
      if (!toolbarColor) {
        return requestAnimationFrame(onColorSchemeChange);
      }

      const mode = matcher.matches ? 'dark' : 'light';
      const selector = `meta[name="theme-color"][media="(prefers-color-scheme: ${mode})"]`;
      const themeColor = document.head.querySelector(selector);
      themeColor?.setAttribute('content', toolbarColor);
    }

    matcher.addEventListener('change', onColorSchemeChange);
    onColorSchemeChange();
  }

  listenLanguageChange() {
    if (!('navigator' in globalThis) || !('document' in globalThis)) {
      return;
    }

    this.transloco.langChanges$
      .pipe(
        tap(lang => {
          document.documentElement.lang = lang;
          document.dir = ['he', 'ar', 'fa', 'ku', 'ps', 'sd', 'ug', 'ur', 'yi'].includes(lang) ? 'rtl' : 'ltr';
        })
      )
      .subscribe();

    this.transloco.setActiveLang(languageCodeNormalizer(navigator.language));
  }
}
