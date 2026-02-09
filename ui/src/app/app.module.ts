import { APP_INITIALIZER, NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';

import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';

import { HttpClient, provideHttpClient, withInterceptorsFromDi } from '@angular/common/http';
import { SettingsService } from './_services/settings.service';

import { MatButtonModule } from '@angular/material/button';
import { MatButtonToggleModule } from '@angular/material/button-toggle';
import { MatCardModule } from '@angular/material/card';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatChipsModule } from '@angular/material/chips';
import { MatNativeDateModule } from '@angular/material/core';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatDialogModule } from '@angular/material/dialog';
import { MatDividerModule } from '@angular/material/divider';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatGridListModule } from '@angular/material/grid-list';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatListModule } from '@angular/material/list';
import { MatMenuModule } from '@angular/material/menu';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { MatSortModule } from '@angular/material/sort';
import { MatTableModule } from '@angular/material/table';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatTooltipModule } from '@angular/material/tooltip';

import { NgbAlertModule, NgbPopoverModule } from '@ng-bootstrap/ng-bootstrap';
import { GaugeModule } from 'angular-gauge';
import { QRCodeComponent } from 'angularx-qrcode';

import { FileUploaderComponent } from './_components/file-uploader/file-uploader.component';
import { FooterComponent } from './_components/footer/footer.component';
import { HeaderComponent } from './_components/header/header.component';
import { FileUploadDialogComponent } from './_dialogs/file-upload-dialog/file-upload-dialog.component';
import { LocationImageDialog } from './_dialogs/image-preview-dialog/image-preview-dialog.component';
import { ImageSelectorDialogComponent } from './_dialogs/image-selector-dialog/image-selector-dialog.component';
import { LocationQRCodeDialog } from './_dialogs/qrcode-dialog/qrcode-dialog.component';
import { LocationSelectorComponent } from './location-selector/location-selector.component';
import { LocationComponent } from './location/location.component';
import { LoginComponent } from './login/login.component';
import { ManageBeerComponent } from './manage/beer/beer.component';
import { ManageBeverageComponent } from './manage/beverage/beverage.component';
import { ManageLocationsComponent } from './manage/locations/locations.component';
import { ManageComponent } from './manage/manage.component';
import { ManagePlaatoKegComponent } from './manage/plaato-keg/plaato-keg.component';
import { ManageTapMonitorsComponent } from './manage/tap-monitors/tap-monitors.component';
import { ManageTapsComponent } from './manage/taps/taps.component';
import { ManageUsersComponent } from './manage/users/users.component';
import { ProfileComponent } from './profile/profile.component';
import { VolumeCalculatorComponent } from './tools/volume-calculator/volume-calculator.component';

import { DndDirective } from './_directives/dnd.directive';
import { ErrorsComponent } from './errors/errors.component';
import { WINDOW_PROVIDERS } from './window.provider';

/**
 * Factory function to initialize settings before the app starts
 */
export function initializeSettings(settingsService: SettingsService) {
  return () => settingsService.loadSettings();
}

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
    ManageTapMonitorsComponent,
    ManagePlaatoKegComponent,
    ManageTapsComponent,
    ManageUsersComponent,
    ProfileComponent,
    VolumeCalculatorComponent,
  ],
  bootstrap: [AppComponent],
  imports: [
    AppRoutingModule,
    BrowserAnimationsModule,
    BrowserModule,
    FormsModule,
    GaugeModule.forRoot(),
    MatButtonModule,
    MatButtonToggleModule,
    MatCardModule,
    MatCheckboxModule,
    MatChipsModule,
    MatDatepickerModule,
    MatDialogModule,
    MatDividerModule,
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
    QRCodeComponent,
    ReactiveFormsModule,
  ],
  providers: [
    HttpClient,
    WINDOW_PROVIDERS,
    provideHttpClient(withInterceptorsFromDi()),
    {
      provide: APP_INITIALIZER,
      useFactory: initializeSettings,
      deps: [SettingsService],
      multi: true,
    },
  ],
})
export class AppModule {}
