import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

import { LocationComponent } from './location/location.component'
import { LocationSelectorComponent } from './location-selector/location-selector.component'
import { LoginComponent } from './login/login.component';
import { ManageBeerComponent } from './manage/beer/beer.component';
import { ManageComponent } from './manage/manage.component'
import { ManageLocationsComponent } from './manage/locations/locations.component';
import { ManageSensorsComponent } from './manage/sensors/sensors.component';
import { ManageTapsComponent } from './manage/taps/taps.component';
import { ManageUsersComponent } from './manage/users/users.component';
import { ProfileComponent } from './profile/profile.component';
import { ErrorsComponent } from './errors/errors.component';

const routes: Routes = [
  {
    path: '',
    component: LocationSelectorComponent,
    data: {
      access: { restricted: false }
    }
  },
  {
    path: 'view/:location',
    component: LocationComponent,
    data: {
      hideHeader: true,
      hideFooter: true,
      access: { restricted: false }
    }
  },
  {
    path: 'login',
    component: LoginComponent,
    data: {
      access: { restricted: false }
    }
  },
  {
    path: 'me',
    component: ProfileComponent
  },
  {
    path: 'manage',
    component: ManageComponent
  },
  {
    path: 'manage/locations',
    component: ManageLocationsComponent
  },
  {
    path: 'manage/sensors',
    component: ManageSensorsComponent
  },
  {
    path: 'manage/taps',
    component: ManageTapsComponent
  },
  {
    path: 'manage/beers',
    component: ManageBeerComponent
  },
  {
    path: 'manage/users',
    component: ManageUsersComponent
  },
  {
    path: 'unauthorized',
    component: ErrorsComponent,
    data: {
      error: "unauthorized",
      access: { restricted: false }
    }
  },
  {
    path: 'forbidden',
    component: ErrorsComponent,
    data: {
      error: "forbidden",
      access: { restricted: false }
    }
  },
  {
    path: 'error',
    component: ErrorsComponent,
    data: {
      error: "unknown",
      access: { restricted: false }
    }
  },
  {
    path: 'not-found',
    component: ErrorsComponent,
    data: {
      error: "notFound",
      access: { restricted: false }
    }
  },
  {
    path: '404',
    component: ErrorsComponent,
    data: {
      error: "notFound",
      access: { restricted: false }
    }
  },
  {path: '**', redirectTo: '/404'}
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
