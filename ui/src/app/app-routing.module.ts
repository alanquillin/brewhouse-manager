import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

import { LocationComponent } from './location/location.component'
import { LocationSelectorComponent } from './location-selector/location-selector.component'
import { ManageComponent } from './manage/manage.component'
import { LoginComponent } from './login/login.component';
import { ManageLocationsComponent } from './manage/locations/locations.component';
import { ProfileComponent } from './profile/profile.component';

const routes: Routes = [
  {
    path: '',
    component: LocationSelectorComponent,
  },
  {
    path: 'view/:location',
    component: LocationComponent,
  },
  {
    path: 'login',
    component: LoginComponent
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
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
