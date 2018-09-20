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
        'node_modules/string.prototype.startswith/startswith.js',
        'node_modules/string.prototype.endswith/endswith.js',
        'node_modules/string.prototype.contains/contains.js',
        'node_modules/console-polyfill/index.js',
        'scripts/polyfills/*.js',
        'node_modules/api-check/dist/api-check.js',
        'node_modules/jquery/dist/jquery.js',
        'node_modules/jquery-ui-dist/jquery-ui.js',
        'node_modules/ua-parser-js/src/ua-parser.js',
        'node_modules/angular/angular.js',
        'scripts/angular-locale_sv.js',
        'node_modules/angular-animate/angular-animate.js',
        'node_modules/angular-cron-jobs/dist/angular-cron-jobs.js',
        'node_modules/angular-messages/angular-messages.js',
        'node_modules/angular-route/angular-route.js',
        'node_modules/angular-mocks/angular-mocks.js',
        'node_modules/angular-ui-bootstrap/dist/ui-bootstrap-tpls.js',
        'node_modules/angular-tree-control/angular-tree-control.js',
        'node_modules/angular-formly/dist/formly.js',
        'node_modules/angular-formly-templates-bootstrap/dist/angular-formly-templates-bootstrap.js',
        'node_modules/angular-smart-table/dist/smart-table.js',
        'node_modules/angular-bootstrap-grid-tree/src/tree-grid-directive.js',
        'node_modules/angular-ui-router/release/angular-ui-router.js',
        'node_modules/angular-cookies/angular-cookies.js ',
        'node_modules/angular-permission/dist/angular-permission.js',
        'node_modules/angular-permission/dist/angular-permission-ui.js',
        'node_modules/angular-translate/dist/angular-translate.js',
        'node_modules/angular-translate-storage-cookie/angular-translate-storage-cookie.js',
        'node_modules/angular-translate-loader-static-files/angular-translate-loader-static-files.js',
        'node_modules/angular-sanitize/angular-sanitize.js',
        'node_modules/angular-bootstrap-contextmenu/contextMenu.js',
        'node_modules/angular-websocket/dist/angular-websocket.js',
        'node_modules/ui-select/dist/select.js',
        'node_modules/bootstrap/dist/js/bootstrap.js',
        'node_modules/@flowjs/ng-flow/dist/ng-flow-standalone.js',
        'bower_components/angular-link-header-parser/release/angular-link-header-parser.js',
        'bower_components/lodash/lodash.js', // required by angular-link-header-parser
        'bower_components/uri-util/dist/uri-util.js', // required by angular-link-header-parser
        'node_modules/marked/lib/marked.js',
        'node_modules/messenger-hubspot/build/js/messenger.js',
        'node_modules/messenger-hubspot/build/js/messenger-theme-flat.js',
        'node_modules/angular-marked/dist/angular-marked.js',
        'node_modules/angular-relative-date/dist/angular-relative-date.js',
        'node_modules/angular-filesize-filter/angular-filesize-filter.js',
        'node_modules/moment/min/moment-with-locales.js',
        'node_modules/angular-date-time-input/src/dateTimeInput.js',
        'node_modules/angular-bootstrap-datetimepicker/src/js/datetimepicker.js',
        'node_modules/angular-bootstrap-datetimepicker/src/js/datetimepicker.templates.js',
        'node_modules/angular-clipboard/angular-clipboard.js',
        'node_modules/angular-resizable/src/angular-resizable.js',
        'node_modules/angular-resource/angular-resource.js',
        'node_modules/jstree/dist/jstree.js',
        'node_modules/ng-js-tree/dist/ngJsTree.js',
        'node_modules/later/later.js',
        'node_modules/prettycron/prettycron.js',

        'scripts/myApp.js',
        'scripts/core/*.js',
        'scripts/profile_maker/*.js',
        'scripts/controllers/*.js',
        'scripts/components/*.js',
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
    browsers: ['Chrome','Chromium', 'Firefox', 'PhantomJS', 'ChromeCanary', 'Safari', 'IE', 'Edge'],

    plugins: [
      'karma-chrome-launcher',
      'karma-firefox-launcher',
      'karma-phantomjs-launcher',
      'karma-safari-launcher',
      'karma-ie-launcher',
      'karma-edge-launcher',
      'karma-jasmine',
      'karma-junit-reporter'
    ],

    junitReporter: {
      outputFile: 'test_out/unit.xml',
      suite: 'unit'
    }
  })
}
