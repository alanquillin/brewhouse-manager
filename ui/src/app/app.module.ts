import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';

import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { FlexLayoutModule } from '@angular/flex-layout';


import { HttpClient } from '@angular/common/http';
import { HttpClientModule } from '@angular/common/http';

import { MatSelectModule } from '@angular/material/select'
import { MatButtonToggleModule } from '@angular/material/button-toggle';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatIconModule} from '@angular/material/icon';
import { MatMenuModule} from '@angular/material/menu';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from "@angular/material/form-field";
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { MatListModule } from '@angular/material/list';
import { MatChipsModule } from '@angular/material/chips';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatButtonModule } from '@angular/material/button';
import { MatTableModule } from '@angular/material/table';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner'; 
import { MatCardModule } from '@angular/material/card';
import { MatProgressBarModule } from '@angular/material/progress-bar'; 
import { MatSidenavModule } from '@angular/material/sidenav';

import { GaugeModule } from 'angular-gauge';

import { LocationComponent } from './location/location.component';
import { LocationSelectorComponent } from './location-selector/location-selector.component';
import { ManageComponent } from './manage/manage.component';

@NgModule({
  declarations: [
    AppComponent,
    LocationComponent,
    LocationSelectorComponent,
    ManageComponent
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    BrowserAnimationsModule,
    HttpClientModule,
    MatSelectModule,
    MatButtonToggleModule,
    MatSlideToggleModule,
    MatIconModule,
    MatMenuModule,
    FormsModule,
    ReactiveFormsModule,
    MatInputModule,
    FlexLayoutModule,
    MatFormFieldModule,
    MatSnackBarModule,
    MatListModule,
    MatChipsModule,
    MatTooltipModule,
    MatButtonModule,
    MatTableModule,
    MatProgressSpinnerModule,
    MatCardModule,
    MatProgressBarModule,
    MatSidenavModule,
    GaugeModule.forRoot()
  ],
  providers: [HttpClient],
  bootstrap: [AppComponent]
})
export class AppModule { }
