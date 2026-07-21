// This file is required by karma.conf.js and loads recursively all the .spec and framework files

import { provideHttpClient, withXhr } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { ANIMATION_MODULE_TYPE, NgModule, NO_ERRORS_SCHEMA } from '@angular/core';
import { getTestBed } from '@angular/core/testing';
import { BrowserTestingModule, platformBrowserTesting } from '@angular/platform-browser/testing';
import { provideRouter } from '@angular/router';
import 'zone.js/testing';

import { WINDOW } from './app/window.provider';

/**
 * Custom testing module that includes global providers needed by all tests.
 * This extends BrowserDynamicTestingModule with additional providers.
 */
@NgModule({
  providers: [
    // Provide the WINDOW token with the actual window object for tests
    { provide: WINDOW, useValue: window },
    // Provide HTTP client for tests
    provideHttpClient(withXhr()),
    provideHttpClientTesting(),
    // Provide router with empty routes for tests
    provideRouter([]),
    // Disable animations for tests
    { provide: ANIMATION_MODULE_TYPE, useValue: 'NoopAnimations' },
  ],
  // Use NO_ERRORS_SCHEMA to ignore unknown elements in templates
  // This allows tests to run even when Angular Material modules aren't imported
  schemas: [NO_ERRORS_SCHEMA],
})
export class AppTestingModule {}

// First, initialize the Angular testing environment with our custom module.
getTestBed().initTestEnvironment(
  [BrowserTestingModule, AppTestingModule],
  platformBrowserTesting(),
  {
    // Apply NO_ERRORS_SCHEMA globally to all tests to ignore unknown elements
    errorOnUnknownElements: false,
    errorOnUnknownProperties: false,
  }
);
