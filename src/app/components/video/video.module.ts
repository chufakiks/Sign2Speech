import {NgModule} from '@angular/core';
import {VideoComponent} from './video.component';
import {provideStates} from '@ngxs/store';
import {VideoState} from '../../core/modules/ngxs/store/video/video.state';
import {PoseState} from '../../modules/pose/pose.state';

@NgModule({
  exports: [VideoComponent],
  imports: [VideoComponent],
  providers: [provideStates([VideoState, PoseState])],
})
export class VideoModule {}
