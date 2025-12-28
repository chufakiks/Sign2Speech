import {AfterViewInit, Component, inject} from '@angular/core';
import {TranslocoService} from '@jsverse/transloco';
import {tap} from 'rxjs/operators';
import {Capacitor} from '@capacitor/core';
import {languageCodeNormalizer} from './core/modules/transloco/languages';
import {Meta} from '@angular/platform-browser';
import {IonApp, IonRouterOutlet} from '@ionic/angular/standalone';
import {getUrlParams} from './core/helpers/url';
import {MediaMatcher} from '@angular/cdk/layout';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss'],
  imports: [IonApp, IonRouterOutlet],
})
export class AppComponent implements AfterViewInit {
  private meta = inject(Meta);
  private transloco = inject(TranslocoService);
  private mediaMatcher = inject(MediaMatcher);

  urlParams = getUrlParams();

  constructor() {
    this.listenLanguageChange();
    this.checkURLEmbedding();
    this.updateToolbarColor();
    this.setPageKeyboardClass();
  }

  async ngAfterViewInit() {
    if (Capacitor.isNativePlatform()) {
      this.meta.updateTag({
        name: 'viewport',
        content:
          'minimum-scale=1.0, maximum-scale=1.0, user-scalable=no, initial-scale=1.0, viewport-fit=cover, width=device-width',
      });

      const {SplashScreen} = await import(
        /* webpackChunkName: "@capacitor/splash-screen" */ '@capacitor/splash-screen'
      );
      await SplashScreen.hide();
    }

    this.initCookieConsent();
  }

  updateToolbarColor() {
    if (!('window' in globalThis)) {
      return;
    }

    const matcher = this.mediaMatcher.matchMedia('(prefers-color-scheme: dark)');

    function onColorSchemeChange(): any {
      const toolbar = document.querySelector('ion-toolbar');
      if (!toolbar) {
        // Try again if the toolbar is not yet available
        return requestAnimationFrame(onColorSchemeChange);
      }

      const toolbarColor = window.getComputedStyle(toolbar).getPropertyValue('--background');
      if (!toolbarColor) {
        // Try again if the color is not yet available
        return requestAnimationFrame(onColorSchemeChange);
      }

      // Update the theme-color meta tag with the toolbar color
      const mode = matcher.matches ? 'dark' : 'light';
      const selector = `meta[name="theme-color"][media="(prefers-color-scheme: ${mode})"]`;
      const themeColor = document.head.querySelector(selector);
      themeColor.setAttribute('content', toolbarColor);
    }

    matcher.addEventListener('change', onColorSchemeChange);
    onColorSchemeChange();
  }

  initCookieConsent() {
    if (!('document' in globalThis)) {
      return Promise.resolve();
    }
    return CookieConsent.run({
      root: 'body',
      autoShow: true,
      hideFromBots: true,

      cookie: {
        name: 'cc_cookie',
        domain: location.hostname,
        path: '/',
        sameSite: 'Lax',
        expiresAfterDays: 182,
      },

      // https://cookieconsent.orestbida.com/reference/configuration-reference.html#guioptions
      guiOptions: {
        consentModal: {
          layout: 'cloud inline',
          position: 'bottom center',
          equalWeightButtons: true,
          flipButtons: false,
        },
        preferencesModal: {
          layout: 'box',
          equalWeightButtons: true,
          flipButtons: false,
        },
      },
      categories: {
        necessary: {
          enabled: true, // this category is enabled by default
          readOnly: true, // this category cannot be disabled
        },
        functionality: {
          enabled: true,
        },
      },

      language: {
        default: 'en',
        translations: {
          en: 'assets/i18n/cookies/en.json',
        },
      },
    });
  }

  listenLanguageChange() {
    const urlParam = this.urlParams.get('lang');

    if (!('navigator' in globalThis) || !('document' in globalThis)) {
      if (urlParam) {
        this.transloco.setActiveLang(urlParam);
      }
      return;
    }

    this.transloco.langChanges$
      .pipe(
        tap(lang => {
          document.documentElement.lang = lang;
          document.dir = ['he', 'ar', 'fa', 'ku', 'ps', 'sd', 'ug', 'ur', 'yi'].includes(lang) ? 'rtl' : 'ltr';

          // Set pre-rendered cloud function path with lang attribute
          const openSearch = Array.from(document.head.children).find(t => t.getAttribute('rel') === 'search');
          if (openSearch) {
            // not available in the test environment sometimes
            openSearch.setAttribute('href', `/opensearch.xml?lang=${lang}`);
          }
        })
      )
      .subscribe();

    this.transloco.setActiveLang(urlParam || languageCodeNormalizer(navigator.language));
  }

  checkURLEmbedding(): void {
    const urlParam = this.urlParams.get('embed');
    if (urlParam !== null) {
      document.body.classList.add('embed');
    }
  }

  async setPageKeyboardClass() {
    if (!Capacitor.isNativePlatform()) {
      return;
    }
    const {Keyboard} = await import(/* webpackChunkName: "@capacitor/keyboard" */ '@capacitor/keyboard');
    const html = document.documentElement;
    const className = 'keyboard-is-open';
    Keyboard.addListener('keyboardWillShow', () => html.classList.add(className));
    Keyboard.addListener('keyboardWillHide', () => html.classList.remove(className));
  }
}
