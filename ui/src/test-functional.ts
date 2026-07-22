// This file is required by karma-functional.conf.js and loads functional test files
// Functional tests run against a real API server in Docker

import { provideHttpClient, withXhr } from '@angular/common/http';
import { ANIMATION_MODULE_TYPE, NgModule, NO_ERRORS_SCHEMA } from '@angular/core';
import { getTestBed } from '@angular/core/testing';
import { BrowserTestingModule, platformBrowserTesting } from '@angular/platform-browser/testing';
import { provideRouter } from '@angular/router';
import 'zone.js/testing';

import { WINDOW } from './app/window.provider';

/**
 * Custom testing module for functional tests.
 * Uses real HTTP client (not testing mock).
 * Chrome is launched with --disable-web-security to allow cross-origin requests.
 */
@NgModule({
  providers: [
    // Provide the WINDOW token pointing to Docker API at localhost:5050
    // Chrome is launched with --disable-web-security to bypass CORS
    {
      provide: WINDOW,
      useValue: {
        location: {
          protocol: 'http:',
          hostname: 'localhost',
          port: '5050',
        },
      } as unknown as Window,
    },
    // Provide real HTTP client (not the testing module)
    provideHttpClient(withXhr()),
    // Provide router with empty routes for tests
    provideRouter([]),
    // Disable animations for tests
    { provide: ANIMATION_MODULE_TYPE, useValue: 'NoopAnimations' },
  ],
  schemas: [NO_ERRORS_SCHEMA],
})
export class FunctionalTestingModule {}

// Initialize the Angular testing environment with our functional testing module
getTestBed().initTestEnvironment(
  [BrowserTestingModule, FunctionalTestingModule],
  platformBrowserTesting(),
  {
    errorOnUnknownElements: false,
    errorOnUnknownProperties: false,
  }
);
