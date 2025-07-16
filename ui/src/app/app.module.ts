import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';

import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';


import { HttpClient } from '@angular/common/http';
import { HttpClientModule } from '@angular/common/http';

import { MatButtonModule } from '@angular/material/button';
import { MatButtonToggleModule } from '@angular/material/button-toggle';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatDialogModule } from '@angular/material/dialog';  
import { MatFormFieldModule } from "@angular/material/form-field";
import { MatGridListModule } from '@angular/material/grid-list';
import { MatIconModule} from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatListModule } from '@angular/material/list';
import { MatMenuModule} from '@angular/material/menu';
import { MatNativeDateModule } from '@angular/material/core';
import { MatProgressBarModule } from '@angular/material/progress-bar'; 
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner'; 
import { MatSelectModule } from '@angular/material/select'
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { MatSortModule } from '@angular/material/sort'; 
import { MatTableModule } from '@angular/material/table';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatCheckboxModule } from '@angular/material/checkbox';

import { GaugeModule } from 'angular-gauge';
import { NgbPopoverModule, NgbAlertModule } from '@ng-bootstrap/ng-bootstrap'
import { QRCodeModule } from 'angularx-qrcode';

import { FileUploadDialogComponent } from './_dialogs/file-upload-dialog/file-upload-dialog.component';
import { FileUploaderComponent } from './_components/file-uploader/file-uploader.component';
import { FooterComponent } from './_components/footer/footer.component';
import { ImageSelectorDialogComponent } from './_dialogs/image-selector-dialog/image-selector-dialog.component';
import { LocationComponent } from './location/location.component';
import { LocationImageDialog } from './_dialogs/image-preview-dialog/image-preview-dialog.component'
import { LocationQRCodeDialog } from './_dialogs/qrcode-dialog/qrcode-dialog.component'
import { LocationSelectorComponent } from './location-selector/location-selector.component';
import { LoginComponent } from './login/login.component';
import { ManageBeerComponent } from './manage/beer/beer.component';
import { ManageBeverageComponent } from './manage/beverage/beverage.component';
import { ManageComponent } from './manage/manage.component';
import { HeaderComponent } from './_components/header/header.component';
import { ManageLocationsComponent } from './manage/locations/locations.component';
import { ManageSensorsComponent } from './manage/sensors/sensors.component';
import { ManageTapsComponent } from './manage/taps/taps.component';
import { ManageUsersComponent } from './manage/users/users.component'
import { ProfileComponent } from './profile/profile.component';
import { VolumeCalculatorComponent } from './tools/volume-calculator/volume-calculator.component';

import { WINDOW_PROVIDERS } from './window.provider';
import { DndDirective } from './_directives/dnd.directive';
import { ErrorsComponent } from './errors/errors.component';

@NgModule({
  declarations: [
    AppComponent,
    DndDirective,
    ErrorsComponent,
    FileUploadDialogComponent,
    FileUploaderComponent,
    HeaderComponent,
    FooterComponent,
    ImageSelectorDialogComponent,
    LocationComponent,
    LocationImageDialog,
    LocationQRCodeDialog,
    LocationSelectorComponent,
    LoginComponent,
    ManageBeerComponent,
    ManageBeverageComponent,
    ManageComponent,
    ManageLocationsComponent,
    ManageSensorsComponent,
    ManageTapsComponent,
    ManageUsersComponent,
    ProfileComponent,
    VolumeCalculatorComponent,
  ],
  imports: [
    AppRoutingModule,
    BrowserAnimationsModule,
    BrowserModule,
    FormsModule,
    GaugeModule.forRoot(),
    HttpClientModule,
    MatButtonModule,
    MatButtonToggleModule,
    MatCardModule,
    MatCheckboxModule,
    MatChipsModule,
    MatDatepickerModule,
    MatDialogModule,
    MatFormFieldModule,
    MatGridListModule,
    MatIconModule,
    MatInputModule,
    MatListModule,
    MatMenuModule,
    MatNativeDateModule,
    MatProgressBarModule,
    MatProgressSpinnerModule,
    MatSelectModule,
    MatSidenavModule,
    MatSlideToggleModule,
    MatSnackBarModule,
    MatSortModule,
    MatTableModule,
    MatToolbarModule,
    MatTooltipModule,
    NgbAlertModule,
    NgbPopoverModule,
    QRCodeModule,
    ReactiveFormsModule,
  ],
  providers: [HttpClient, WINDOW_PROVIDERS],
  bootstrap: [AppComponent]
})
export class AppModule { }
