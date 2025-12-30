import {AfterViewInit, Component, ElementRef, HostBinding, inject, Input, viewChild} from '@angular/core';
import {Store} from '@ngxs/store';
import {firstValueFrom} from 'rxjs';
import {VideoSettings, VideoStateModel} from '../../core/modules/ngxs/store/video/video.state';
import Stats from 'stats.js';
import {distinctUntilChanged, filter, map, takeUntil, tap} from 'rxjs/operators';
import {BaseComponent} from '../base/base.component';
import {wait} from '../../core/helpers/wait/wait';
import {LoadPoseEstimationModel, PoseVideoFrame} from '../../modules/pose/pose.actions';
import {PoseStateModel} from '../../modules/pose/pose.state';
import {SettingsStateModel} from '../../modules/settings/settings.state';
import {IonIcon} from '@ionic/angular/standalone';
import {VideoControlsComponent} from './video-controls/video-controls.component';
import {addIcons} from 'ionicons';
import {playCircleOutline} from 'ionicons/icons';
import {AsyncPipe} from '@angular/common';
import {TranslocoDirective, TranslocoPipe} from '@jsverse/transloco';

@Component({
  selector: 'app-video',
  templateUrl: './video.component.html',
  styleUrls: ['./video.component.scss'],
  imports: [VideoControlsComponent, IonIcon, AsyncPipe, TranslocoPipe, TranslocoDirective],
})
export class VideoComponent extends BaseComponent implements AfterViewInit {
  private store = inject(Store);

  settingsState$ = this.store.select<SettingsStateModel>(state => state.settings);

  videoState$ = this.store.select<VideoStateModel>(state => state.video);
  poseState$ = this.store.select<PoseStateModel>(state => state.pose);
  signingProbability$ = this.store.select<number>(state => state.detector?.signingProbability ?? 0);

  private elementRef = inject(ElementRef);

  readonly videoEl = viewChild<ElementRef<HTMLVideoElement>>('video');
  readonly canvasEl = viewChild<ElementRef<HTMLCanvasElement>>('canvas');
  readonly statsEl = viewChild<ElementRef>('stats');
  appRootEl!: HTMLElement;

  @HostBinding('class') aspectRatio = 'aspect-16-9';

  @Input() displayFps = true;
  @Input() displayControls = true;

  canvasCtx!: CanvasRenderingContext2D;

  videoEnded = false;

  fpsStats = new Stats();
  signingStats = new Stats();

  constructor() {
    super();

    if ('document' in globalThis) {
      this.appRootEl = document.querySelector('ion-app') ?? document.body;
    }

    addIcons({playCircleOutline});
  }

  ngAfterViewInit(): void {
    const videoEl = this.videoEl();
    this.setCamera();
    this.setStats();
    this.trackPose();

    this.canvasCtx = this.canvasEl().nativeElement.getContext('2d');
    this.drawChanges();

    this.preloadPoseEstimationModel();
    videoEl.nativeElement.addEventListener('loadeddata', this.appLoop.bind(this));
    videoEl.nativeElement.addEventListener('ended', () => (this.videoEnded = true));

    const resizeObserver = new ResizeObserver(this.scaleCanvas.bind(this));
    resizeObserver.observe(this.elementRef.nativeElement);
    resizeObserver.observe(this.appRootEl);
  }

  async appLoop(): Promise<void> {
    const video = this.videoEl().nativeElement;
    const poseAction = new PoseVideoFrame(video);

    let lastTime = null;
    while (true) {
      if (video.readyState === 0) {
        break;
      }

      if (video.currentTime !== lastTime) {
        lastTime = video.currentTime;
        await firstValueFrom(this.store.dispatch(poseAction));
      }

      await wait(0);
    }
  }

  setCamera(): void {
    const video = this.videoEl().nativeElement;
    video.muted = true;
    video.addEventListener('loadedmetadata', () => video.play());

    this.videoState$
      .pipe(
        tap(({camera, src}) => {
          this.videoEnded = false;
          video.src = src || '';
          video.srcObject = camera;
        }),
        takeUntil(this.ngUnsubscribe)
      )
      .subscribe();

    this.videoState$
      .pipe(
        map(state => state.videoSettings),
        filter(Boolean),
        tap(({width, height}) => {
          const canvasEl = this.canvasEl();
          canvasEl.nativeElement.width = width;
          canvasEl.nativeElement.height = height;
          requestAnimationFrame(this.scaleCanvas.bind(this));
        }),
        tap((settings: VideoSettings) => (this.aspectRatio = 'aspect-' + settings.aspectRatio)),
        takeUntil(this.ngUnsubscribe)
      )
      .subscribe();
  }

  scaleCanvas(): void {
    requestAnimationFrame(() => {
      const bbox = this.elementRef.nativeElement.getBoundingClientRect();
      const documentBbox = this.appRootEl.getBoundingClientRect();

      const width = Math.min(bbox.width, documentBbox.width);
      const canvasEl = this.canvasEl().nativeElement;
      const scale = width / canvasEl.width;
      canvasEl.style.transform = `scale(-${scale}, ${scale}) translateX(-100%)`;

      this.elementRef.nativeElement.style.height = canvasEl.height * scale + 'px';
      canvasEl.parentElement.style.width = width + 'px';
    });
  }

  trackPose(): void {
    this.poseState$
      .pipe(
        map(state => state.pose),
        filter(Boolean),
        tap(() => {
          this.fpsStats.end();
          this.fpsStats.begin();
        }),
        takeUntil(this.ngUnsubscribe)
      )
      .subscribe();
  }

  preloadPoseEstimationModel(): void {
    this.store.dispatch(LoadPoseEstimationModel);
  }

  drawChanges(): void {
    const ctx = this.canvasCtx;
    const canvas = ctx.canvas;

    this.poseState$
      .pipe(
        filter(state => !!state.pose),
        tap(poseState => {
          ctx.clearRect(0, 0, canvas.width, canvas.height);

          // Draw video
          ctx.drawImage(poseState.pose.image, 0, 0, canvas.width, canvas.height);
        }),
        takeUntil(this.ngUnsubscribe)
      )
      .subscribe();
  }

  setStats(): void {
    this.fpsStats.showPanel(0);
    this.fpsStats.dom.style.position = 'absolute';
    this.statsEl().nativeElement.appendChild(this.fpsStats.dom);

    if (!this.displayFps) {
      this.fpsStats.dom.style.display = 'none';
    }

    const signingPanel = new Stats.Panel('Signing', '#ff8', '#221');
    this.signingStats.dom.innerHTML = '';
    this.signingStats.addPanel(signingPanel);
    this.signingStats.showPanel(0);
    this.signingStats.dom.style.position = 'absolute';
    this.signingStats.dom.style.left = '80px';
    this.statsEl().nativeElement.appendChild(this.signingStats.dom);

    this.setDetectorListener(signingPanel);
  }

  setDetectorListener(panel: Stats.Panel): void {
    this.signingProbability$
      .pipe(
        tap(v => panel.update(v * 100, 100)),
        takeUntil(this.ngUnsubscribe)
      )
      .subscribe();

    this.settingsState$
      .pipe(
        map(settings => settings.detectSign),
        distinctUntilChanged(),
        tap(detectSign => {
          this.signingStats.dom.style.display = detectSign ? 'block' : 'none';
        }),
        takeUntil(this.ngUnsubscribe)
      )
      .subscribe();
  }

  replayVideo() {
    this.videoEnded = false;
    const videoEl = this.videoEl().nativeElement;
    videoEl.currentTime = 0;
    return videoEl.play();
  }
}
