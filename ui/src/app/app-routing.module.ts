import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

import { LocationComponent } from './location/location.component'
import { LocationSelectorComponent } from './location-selector/location-selector.component'
import { ManagementComponent } from './manage/manage.component'

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
    path: 'manage',
    component: ManagementComponent
  },
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
