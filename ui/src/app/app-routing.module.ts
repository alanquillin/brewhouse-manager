import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

import { LocationComponent } from './location/location.component'
import { LocationSelectorComponent } from './location-selector/location-selector.component'
import { LoginComponent } from './login/login.component';
import { ManageBeerComponent } from './manage/beer/beer.component';
import { ManageBeverageComponent } from './manage/beverage/beverage.component';
import { ManageComponent } from './manage/manage.component'
import { ManageLocationsComponent } from './manage/locations/locations.component';
import { ManageSensorsComponent } from './manage/sensors/sensors.component';
import { ManagePlaatoKegComponent } from './manage/plaato-keg/plaato-keg.component';
import { ManageTapsComponent } from './manage/taps/taps.component';
import { ManageUsersComponent } from './manage/users/users.component';
import { ProfileComponent } from './profile/profile.component';
import { ErrorsComponent } from './errors/errors.component';
import { VolumeCalculatorComponent } from './tools/volume-calculator/volume-calculator.component';
import { PlaatoKegFeatureGuard } from './_guards/plaato-keg-feature.guard';

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
      emptyHeader: true,
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
    path: 'manage/plaato_kegs',
    component: ManagePlaatoKegComponent,
    canActivate: [PlaatoKegFeatureGuard]
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
    path: 'manage/beverages',
    component: ManageBeverageComponent
  },
  {
    path: 'manage/users',
    component: ManageUsersComponent
  },
  {
    path: 'tools/volume_calculator',
    component: VolumeCalculatorComponent,
    data: {
      access: { restricted: false }
    }
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
