import { Component, OnInit, inject } from '@angular/core';
import { Title } from '@angular/platform-browser';
import { RouterOutlet } from '@angular/router';
import { map } from 'rxjs/operators';

import { ConfigService } from './_services/config.service';
import { toBoolean } from './utils/helpers';

import * as _ from 'lodash';
import { DataError, DataService } from './_services/data.service';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss'],
  standalone: false,
})
export class AppComponent implements OnInit {
  private dataService = inject(DataService);
  private configService = inject(ConfigService);
  private titleService = inject(Title);

  title = 'Brewhouse Manager';
  hideHeader = false;
  emptyHeader = false;
  hideFooter = false;
  restricted = true;
  routeData: any;

  setConfig(data: any): void {
    this.title = _.get(data, 'title', 'brewhouse-manager');
    this.hideHeader = toBoolean(_.get(data, 'hideHeader', false));
    this.emptyHeader = toBoolean(_.get(data, 'emptyHeader', false));
    this.hideFooter = toBoolean(_.get(data, 'hideFooter', false));
    this.restricted = toBoolean(_.get(data, 'access.restricted', true));

    this.titleService.setTitle(this.title);
  }

  onActivate(outlet: RouterOutlet): void {
    outlet.activatedRoute.data
      .pipe(
        map(data => {
          this.routeData = data;
          this.setConfig(data);
        })
      )
      .toPromise()
      .then();
  }

  ngOnInit(): void {
    this.configService.updated.subscribe((data: any) => {
      this.setConfig(_.merge(this.routeData, data));
    });

    this.dataService.unauthorized.subscribe((_err: DataError) => {
      if (this.restricted) {
        window.location.href = '/login';
      }
    });
  }
}
