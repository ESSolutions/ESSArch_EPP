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

var gulp = require('gulp')
var rev = require('gulp-rev');
var revDel = require('rev-del');
var sass = require('gulp-sass');
var autoprefixer = require('gulp-autoprefixer');
var ngConstant = require('gulp-ng-constant');
var concat = require('gulp-concat');
var concatCss = require('gulp-concat-css');
var gulpif = require('gulp-if');
var ngAnnotate = require('gulp-ng-annotate');
var templateCache = require('gulp-angular-templatecache');
var plumber = require('gulp-plumber');
var rename = require('gulp-rename');
var uglify = require('gulp-uglify');
var stripDebug = require('gulp-strip-debug');
var cleanCSS = require('gulp-clean-css');
var header = require('gulp-header');
var fs = require('fs');
var path = require('path');
var argv = require('yargs').argv;
var isProduction = (argv.production === undefined) ? false : true;

var core = process.env.EC_FRONTEND;
var coreHtmlFiles = [path.join(core, 'views/**/*.html')];
var coreJsFiles = [path.join(core, 'scripts/**/*.js')];
var coreTestFiles = [path.join(core, 'tests/*.js')];
var coreCssFiles = path.join(core, 'styles');

var jsPolyfillFiles = [
    'node_modules/string.prototype.startswith/startswith.js',
    'node_modules/string.prototype.endswith/endswith.js',
    'node_modules/string.prototype.contains/contains.js',
    'node_modules/console-polyfill/index.js',
    'scripts/polyfills/*.js',
]
var jsVendorFiles = [
        'node_modules/api-check/dist/api-check.js',
        'node_modules/jquery/dist/jquery.js',
        'node_modules/lodash/lodash.js',
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
        'node_modules/uri-util/dist/uri-util.js', // required by angular-link-header-parser
        'node_modules/angular-link-header-parser/src/angular-link-header-parser.js',
        'node_modules/marked/lib/marked.js',
        'node_modules/messenger-hubspot/build/js/messenger.js',
        'node_modules/messenger-hubspot/build/js/messenger-theme-flat.js',
        'node_modules/angular-marked/dist/angular-marked.js',
        'node_modules/angular-relative-date/dist/angular-relative-date.js',
        'node_modules/angular-filesize-filter/angular-filesize-filter.js',
        'node_modules/moment/min/moment-with-locales.js',
        'node_modules/angular-date-time-input/src/dateTimeInput.js',
        'node_modules/angularjs-bootstrap-datetimepicker/src/js/datetimepicker.js',
        'node_modules/angularjs-bootstrap-datetimepicker/src/js/datetimepicker.templates.js',
        'node_modules/angular-clipboard/angular-clipboard.js',
        'node_modules/angular-resizable/src/angular-resizable.js',
        'node_modules/angular-resource/angular-resource.js',
        'node_modules/jstree/dist/jstree.js',
        'node_modules/ng-js-tree/dist/ngJsTree.js',
        'node_modules/later/later.js',
        'node_modules/prettycron/prettycron.js',
    ],
    jsFiles = [
        'scripts/essarch.module.js', 'scripts/modules/*.module.js', 'scripts/core/*.js', 'scripts/profile_maker/*.js', 'scripts/controllers/*.js', 'scripts/components/*.js',
        'scripts/services/*.js', 'scripts/directives/*.js', 'scripts/configs/*.js'
    ],
    jsDest = 'scripts',
    cssFiles = [
        coreCssFiles + "/**/*.scss",
        'styles/modules/reception.scss',
        'styles/modules/index.scss',
        'styles/modules/login.scss',
        'styles/modules/my_page.scss',
        'styles/modules/colors.scss',
        'styles/modules/mixins.scss',
        'styles/modules/tree_control.scss',
        'styles/modules/profile_maker.scss',
        'styles/modules/profile_editor.scss',
        'styles/modules/notifications.scss',
        'styles/modules/search.scss',
        'styles/modules/positions.scss',
        'styles/modules/utils.scss',
        'styles/modules/classification_structure_editor.scss',
        'styles/styles.scss'
    ],
    cssDest = 'styles';

var licenseString = fs.readFileSync('license.txt');

var buildPolyfills= function() {
    return gulp.src(jsPolyfillFiles, {allowEmpty: true, sourcemaps: true})
        .pipe(plumber(function(error) {
          // output an error message

          console.error('error (' + error.plugin + '): ' + error.message);
          // emit the end event, to properly end the task
          this.emit('end');
        }))
        .pipe(ngAnnotate())
        .pipe(concat('polyfills.min.js'))
        .pipe(gulpif(isProduction, uglify()))
        .pipe(gulp.dest(jsDest, {sourcemaps: '.'}));
};

var buildCoreTemplates = function() {
    return gulp.src(coreHtmlFiles, {allowEmpty: true})
        .pipe(templateCache({
            standalone: true,
            transformUrl: function(url) {
                // Remove leading slash which occurs in gulp 4
                // https://github.com/miickel/gulp-angular-templatecache/issues/153
                return url.replace(/^(\\|\/)+/g, '');
            }
        }))
        .pipe(gulp.dest('scripts/core'));
}

var buildCoreScripts = function() {
    return gulp.src(coreJsFiles, {allowEmpty: true, sourcemaps:true})
        .pipe(concat('scripts.js'))
        .pipe(gulp.dest('scripts/core', {sourcemaps: true}));
}

var buildCoreTests = function() {
    return gulp.src(coreTestFiles, {allowEmpty: true})
        .pipe(concat('tests.js'))
        .pipe(gulp.dest('tests/core'));
}

var buildScripts = function() {
    return gulp.src(jsFiles, {allowEmpty: true, sourcemaps: true})
        .pipe(plumber(function(error) {
          // output an error message

          console.error('error (' + error.plugin + '): ' + error.message);
          // emit the end event, to properly end the task
          this.emit('end');
        }))
        .pipe(ngAnnotate())
        .pipe(concat('scripts.min.js'))
        .pipe(gulpif(isProduction, stripDebug()))
        .pipe(gulpif(isProduction, uglify()))
        .pipe(header('/*\n'+licenseString+'*/\n'))
        .pipe(gulp.dest(jsDest, {sourcemaps: '.'}));
};

var buildVendors = function() {
    return gulp.src(jsVendorFiles, {allowEmpty: true, sourcemaps: true})
        .pipe(plumber(function(error) {
          // output an error message

          console.error('error (' + error.plugin + '): ' + error.message);
          // emit the end event, to properly end the task
          this.emit('end');
        }))
        .pipe(ngAnnotate())
        .pipe(concat('vendors.min.js'))
        .pipe(gulpif(isProduction, stripDebug()))
        .pipe(gulpif(isProduction, uglify()))
        .pipe(gulp.dest(jsDest, {sourcemaps: '.'}));
};

var compileSass = function() {
 return gulp.src('styles/styles.scss', {allowEmpty: true, sourcemaps: true})
    .pipe(sass({includePaths: coreCssFiles}).on('error', sass.logError))
    .pipe(autoprefixer({
        browsers: ['>0%']
    }))
    .pipe(cleanCSS({
      cleanupCharsets: true, // controls `@charset` moving to the front of a stylesheet; defaults to `true`
      normalizeUrls: true, // controls URL normalization; defaults to `true`
      optimizeBackground: true, // controls `background` property optimizatons; defaults to `true`
      optimizeBorderRadius: true, // controls `border-radius` property optimizatons; defaults to `true`
      optimizeFilter: true, // controls `filter` property optimizatons; defaults to `true`
      optimizeFontWeight: true, // controls `font-weight` property optimizatons; defaults to `true`
      optimizeOutline: true, // controls `outline` property optimizatons; defaults to `true`
      removeNegativePaddings: true, // controls removing negative paddings; defaults to `true`
      removeQuotes: true, // controls removing quotes when unnecessary; defaults to `true`
      removeWhitespace: true, // controls removing unused whitespace; defaults to `true`
      replaceMultipleZeros: true, // contols removing redundant zeros; defaults to `true`
      replaceTimeUnits: true, // controls replacing time units with shorter values; defaults to `true`
      replaceZeroUnits: true, // controls replacing zero values with units; defaults to `true`
      roundingPrecision: false, // rounds pixel values to `N` decimal places; `false` disables rounding; defaults to `false`
      selectorsSortingMethod: 'standard', // denotes selector sorting method; can be `natural` or `standard`; defaults to `standard`
      keepSpecialComments: 0, // denotes a number of /*! ... */ comments preserved; defaults to `all`
      tidyAtRules: true, // controls at-rules (e.g. `@charset`, `@import`) optimizing; defaults to `true`
      tidyBlockScopes: true, // controls block scopes (e.g. `@media`) optimizing; defaults to `true`
      tidySelectors: true, // controls selectors optimizing; defaults to `true`,
      inline: ['all'], // enables all inlining, same as ['local', 'remote']
      transform: function () {} // defines a callback for fine-grained property optimization; defaults to no-op
    }))
    .pipe(gulp.dest('styles', {sourcemaps: '.'}));
};

var buildRevManifest = function() {
    return gulp.src(['styles/styles.css', 'styles/styles.css.map', 'scripts/scripts.min.js', 'scripts/scripts.min.js.map', 'scripts/polyfills.min.js', 'scripts/polyfills.min.js.map', 'scripts/vendors.min.js', 'scripts/vendors.min.js.map'], {allowEmpty: true})
        .pipe(gulp.dest('build'))  // copy original assets to build dir
        .pipe(rev())
        .pipe(gulp.dest('build'))  // write rev'd assets to build dir
        .pipe(rev.manifest())
        .pipe(revDel({dest: 'build'}))
        .pipe(gulp.dest('build'))  // write manifest to build dir
}

var copyIcons = function() {
    return gulp.src('node_modules/@fortawesome/fontawesome-free/webfonts/**.*', {allowEmpty: true})
        .pipe(gulp.dest('webfonts'));
};
var copyImages = function() {
    return gulp.src('node_modules/angular-tree-control/images/**.*', {allowEmpty: true}) 
        .pipe(gulp.dest('images')); 
};
var copyImagesJstree = function() {
    return gulp.src('node_modules/jstree/dist/themes/default/**.{png,gif}')
        .pipe(gulp.dest('build'));
};
var configConstants = function() {
    var myConfig = require('./scripts/configs/config.json');
    if(isProduction) {
        var envConfig = myConfig["production"];
    } else {
        var envConfig = myConfig["development"];
    }
    return ngConstant({
        name: 'essarch.appConfig',
        constants: envConfig,
        stream: true
    })
    .pipe(rename('essarch.config.js'))
    .pipe(gulp.dest('./scripts/configs'));
};

var permissionConfig = function() {
    var permissionConfig = require('./scripts/configs/permissions.json');
    var envConfig = permissionConfig;
    return ngConstant({
        name: 'permission.config',
        constants: envConfig,
        stream: true
    })
    .pipe(rename('permission.config.js'))
    .pipe(gulp.dest('./scripts/configs'));
};

gulp.task('icons', copyIcons);
gulp.task('images', copyImages);
gulp.task('jstree_images', copyImagesJstree);
gulp.task('polyfills', buildPolyfills);
gulp.task('core_templates', buildCoreTemplates);
gulp.task('core_scripts', buildCoreScripts);
gulp.task('core_tests', buildCoreTests);
gulp.task('scripts', buildScripts);
gulp.task('vendors', buildVendors);
gulp.task('sass', compileSass);
gulp.task('rev', buildRevManifest);
gulp.task('config', configConstants);
gulp.task('permission_config', permissionConfig);

gulp.task('default', gulp.series(
    gulp.parallel(
        gulp.series(
            gulp.parallel('config', 'permission_config'),
            gulp.parallel('core_templates', 'core_scripts','core_tests'),
            gulp.parallel('icons', 'jstree_images', 'images', 'polyfills', 'scripts'),
        ),
        'sass',
        'vendors'
    ),
    'rev',
));


gulp.task('watch', function(){
    gulp.watch(coreHtmlFiles, gulp.series('core_templates', 'rev'));
    gulp.watch(coreJsFiles, gulp.series('core_scripts', 'rev'));
    gulp.watch(coreTestFiles, gulp.series('core_tests', 'rev'));
    gulp.watch(jsFiles, gulp.series('scripts', 'rev'));
    gulp.watch(jsPolyfillFiles, gulp.series('polyfills', 'rev'));
    gulp.watch(jsVendorFiles, gulp.series('vendors', 'rev'));
    gulp.watch(cssFiles, gulp.series('sass', 'rev'));
})
