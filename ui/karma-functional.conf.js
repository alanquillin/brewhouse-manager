// Karma configuration for functional tests
// These tests run against a live API server in Docker
// Start the API with: make test-api-up (from the api/tests/api directory)

module.exports = function (config) {
  config.set({
    basePath: '',
    frameworks: ['jasmine', '@angular-devkit/build-angular'],
    plugins: [
      require('karma-jasmine'),
      require('karma-chrome-launcher'),
      require('karma-jasmine-html-reporter'),
      require('karma-coverage'),
    ],
    client: {
      jasmine: {
        // Longer timeout for API calls
        timeoutInterval: 30000,
      },
      clearContext: false,
    },
    jasmineHtmlReporter: {
      suppressAll: true,
    },
    coverageReporter: {
      dir: require('path').join(__dirname, './coverage/brewhouse-manager-functional'),
      subdir: '.',
      reporters: [{ type: 'html' }, { type: 'text-summary' }],
    },
    reporters: ['progress', 'kjhtml'],
    port: 9877, // Different port from unit tests
    colors: true,
    logLevel: config.LOG_INFO,
    autoWatch: true,
    // Use custom Chrome launcher with disabled web security for functional tests
    // This allows cross-origin requests to the Docker API at localhost:5050
    browsers: ['ChromeHeadlessNoSandbox'],
    customLaunchers: {
      ChromeHeadlessNoSandbox: {
        base: 'ChromeHeadless',
        flags: [
          '--no-sandbox',
          '--disable-web-security',
          '--disable-gpu',
          '--disable-site-isolation-trials',
          '--disable-features=OutOfBlinkCors,BlockInsecurePrivateNetworkRequests',
          '--user-data-dir=/tmp/chrome-functional-test',
        ],
      },
      ChromeNoSecurity: {
        base: 'Chrome',
        flags: [
          '--disable-web-security',
          '--disable-site-isolation-trials',
          '--disable-features=OutOfBlinkCors,BlockInsecurePrivateNetworkRequests',
          '--user-data-dir=/tmp/chrome-functional-test',
        ],
      },
    },
    singleRun: true,
    restartOnFileChange: false,
    // Only include functional test files
    files: [
      // Angular core files are handled by the build-angular framework
    ],
    // Custom timeout for API calls
    browserNoActivityTimeout: 60000,
    browserDisconnectTimeout: 30000,
    captureTimeout: 60000,
  });
};
