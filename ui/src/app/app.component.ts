import { Component, OnInit } from '@angular/core';
import { Title } from '@angular/platform-browser';
import { Router  , ActivatedRoute, RouterOutlet } from '@angular/router';
import {map} from 'rxjs/operators';

import { ConfigService } from './_services/config.service';
import { toBoolean } from './utils/helpers';

import * as _ from 'lodash';
import { DataError, DataService } from './data.service';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent implements OnInit {
  title = 'Brewhouse Manager';
  hideHeader: boolean = false;
  hideFooter: boolean = false;
  restricted: boolean = true;
  routeData: any;

  constructor(private dataService: DataService, private configService: ConfigService, private titleService: Title){}

  setConfig(data: any): void {
    this.title = _.get(data, "title", 'brewhouse-manager');
    this.hideHeader = toBoolean(_.get(data, "hideHeader", false));
    this.hideFooter = toBoolean(_.get(data, "hideFooter", false));
    this.restricted = toBoolean(_.get(data, "access.restricted", true))

    this.titleService.setTitle(this.title);
  }

  onActivate(outlet: RouterOutlet): void {
    outlet.activatedRoute.data.pipe(map(data => {
      this.routeData = data;
      this.setConfig(data);
    })).toPromise().then();
  }

  ngOnInit(): void {
    this.configService.updated.subscribe((data: any) => {
      this.setConfig(_.merge(this.routeData, data));
    })

    this.dataService.unauthorized.subscribe((err: DataError) => {
      if (this.restricted) {
        window.location.href = "/login";
      }
    })
  }
}
