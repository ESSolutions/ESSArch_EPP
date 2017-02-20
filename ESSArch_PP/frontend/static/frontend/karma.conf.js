/*
    ESSArch is an open source archiving and digital preservation system

    ESSArch Preservation Platform (EPP)
    Copyright (C) 2005-2017 ES Solutions AB

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program. If not, see <http://www.gnu.org/licenses/>.

    Contact information:
    Web - http://www.essolutions.se
    Email - essarch@essolutions.se
*/

// Karma configuration
// Generated on Wed Jan 04 2017 15:48:10 GMT+0100 (CET)

module.exports = function(config) {
  config.set({

    // base path that will be used to resolve all patterns (eg. files, exclude)
    basePath: '.',


    // frameworks to use
    // available frameworks: https://npmjs.org/browse/keyword/karma-adapter
    frameworks: ['jasmine'],


    // list of files / patterns to load in the browser
    files: [
        'scripts/bower_components/api-check/dist/api-check.js',
        'scripts/bower_components/jquery/dist/jquery.js',
        'scripts/bower_components/jquery-ui/jquery-ui.js',
        'scripts/bower_components/angular/angular.js',
        'scripts/bower_components/angular-animate/angular-animate.js',
        'scripts/bower_components/angular-messages/angular-messages.js',
        'scripts/bower_components/angular-route/angular-route.js',
        'scripts/bower_components/angular-mocks/angular-mocks.js',
        'scripts/bower_components/angular-bootstrap/ui-bootstrap-tpls.js',
        'scripts/bower_components/angular-tree-control/angular-tree-control.js',
        'scripts/bower_components/angular-formly/dist/formly.js',
        'scripts/bower_components/angular-formly-templates-bootstrap/dist/angular-formly-templates-bootstrap.js',
        'scripts/bower_components/angular-smart-table/dist/smart-table.js',
        'scripts/bower_components/angular-bootstrap-grid-tree/src/tree-grid-directive.js',
        'scripts/bower_components/angular-ui-router/release/angular-ui-router.js',
        'scripts/bower_components/angular-cookies/angular-cookies.js ',
        'scripts/bower_components/angular-permission/dist/angular-permission.js',
        'scripts/bower_components/angular-translate/angular-translate.js',
        'scripts/bower_components/angular-translate-storage-cookie/angular-translate-storage-cookie.js',
        'scripts/bower_components/angular-translate-loader-static-files/angular-translate-loader-static-files.js',
        'scripts/bower_components/angular-sanitize/angular-sanitize.js',
        'scripts/bower_components/angular-bootstrap-contextmenu/contextMenu.js',
        'scripts/bower_components/angular-ui-select/dist/select.js',
        'scripts/bower_components/bootstrap/dist/js/bootstrap.js',
        'scripts/bower_components/ng-flow/dist/ng-flow-standalone.js',

        'node_modules/moment/min/moment-with-locales.js',
        'node_modules/angular-date-time-input/src/dateTimeInput.js',
        'node_modules/angular-bootstrap-datetimepicker/src/js/datetimepicker.js',
        'node_modules/angular-bootstrap-datetimepicker/src/js/datetimepicker.templates.js',

        'scripts/myApp.js',
        'scripts/controllers/*.js',
        'scripts/services/*.js',
        'scripts/directives/*.js',
        'scripts/configs/*.js',

        'tests/*.js',
    ],

    // enable / disable watching file and executing tests whenever any file changes
    autoWatch: true,

    // time (ms) browsers wait for messages before disconnecting
    browserNoActivityTimeout: 30000,

    // start these browsers
    // available browser launchers: https://npmjs.org/browse/keyword/karma-launcher
    browsers: ['Chrome','Chromium', 'Firefox', 'PhantomJS', 'ChromeCanary', 'Safari'],

    plugins: [
      'karma-chrome-launcher',
      'karma-firefox-launcher',
      'karma-phantomjs-launcher',
      'karma-safari-launcher',
      'karma-jasmine',
      'karma-junit-reporter'
    ],

    junitReporter: {
      outputFile: 'test_out/unit.xml',
      suite: 'unit'
    }
  })
}
