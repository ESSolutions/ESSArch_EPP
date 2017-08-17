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

angular.module('myApp', ['ngRoute', 'treeControl', 'ui.bootstrap', 'formly', 'formlyBootstrap', 'smart-table', 'treeGrid', 'ui.router', 'ngCookies', 'permission', 'pascalprecht.translate', 'ngSanitize', 'ui.bootstrap.contextMenu', 'ui.select', 'flow', 'ui.bootstrap.datetimepicker', 'ui.dateTimeInput', 'ngAnimate', 'ngMessages', 'myApp.config', 'ig.linkHeaderParser', 'hc.marked', 'ngFilesizeFilter', 'angular-clipboard', "ngResource"])
.config(function($routeProvider, formlyConfigProvider, $stateProvider, $urlRouterProvider, $rootScopeProvider, $uibTooltipProvider) {
    $stateProvider
    .state('home', {
        url: '/',
        templateUrl: '/static/frontend/views/home.html',
    })
    .state('login', {
        url: '/login',
        templateUrl: '/static/frontend/views/login.html',
        controller: 'LoginCtrl as vm',
        resolve: {
            authenticated: ['djangoAuth', function(djangoAuth){
                return djangoAuth.authenticationStatus();
            }],
        }
    })
    .state('logout', {
        url: '/logout',
        templateUrl: '/static/frontend/views/logout.html',
        controller: 'LogoutCtrl as vm',
        resolve: {
            authenticated: ['djangoAuth', function(djangoAuth){
                return djangoAuth.authenticationStatus();
            }],
        }
    })
    .state('home.userSettings', {
        url: 'user-settings',
        templateUrl: '/static/frontend/views/user_settings.html',
        controller: 'UserSettingsCtrl as vm',
        resolve: {
            authenticated: ['djangoAuth', function(djangoAuth){
                return djangoAuth.authenticationStatus();
            }],
        }
    })
    .state('home.myPage', {
        url: 'my-page',
        templateUrl: '/static/frontend/views/my_page.html',
        controller: 'MyPageCtrl as vm',
        resolve: {
            authenticated: ['djangoAuth', function(djangoAuth){
                return djangoAuth.authenticationStatus();
            }],
        }
    })
    .state('home.versionInfo', {
        url: 'version',
        templateUrl: '/static/frontend/views/version_info.html',
        controller: 'VersionCtrl as vm',
        resolve: {
            authenticated: ['djangoAuth', function(djangoAuth){
                return djangoAuth.authenticationStatus();
            }],
        }
    })
    .state('home.info', {
        url: 'info',
        templateUrl: '/static/frontend/views/essarch_info.html',
        controller: 'InfoCtrl as vm',
        resolve: {
            authenticated: ['djangoAuth', function(djangoAuth){
                return djangoAuth.authenticationStatus();
            }],
        }
    })
    .state('home.ingest', {
        url: 'ingest',
        templateUrl: '/static/frontend/views/ingest.html',
        redirectTo: 'home.ingest.reception',
        controller: 'ReceptionCtrl as vm',
        resolve: {
            authenticated: ['djangoAuth', function(djangoAuth){
                return djangoAuth.authenticationStatus();
            }],
        }
    })
    .state('home.ingest.reception', {
        url: '/reception',
        templateUrl: '/static/frontend/views/reception.html',
        controller: 'ReceptionCtrl as vm',
        resolve: {
            authenticated: ['djangoAuth', function(djangoAuth){
                return djangoAuth.authenticationStatus();
            }],
        }
    })
    .state('home.ingest.ipApproval', {
        url: '/approval',
        templateUrl: '/static/frontend/views/ip_approval.html',
        controller: 'IpApprovalCtrl as vm',
        resolve: {
            authenticated: ['djangoAuth', function(djangoAuth){
                return djangoAuth.authenticationStatus();
            }],
        }
    })
    .state('home.ingest.workarea', {
        url: '/workarea',
        templateUrl: '/static/frontend/views/ingest_workarea.html',
        controller: 'IngestWorkareaCtrl as vm',
        resolve: {
            authenticated: ['djangoAuth', function(djangoAuth){
                return djangoAuth.authenticationStatus();
            }],
        }
    })
    .state('home.access', {
        url: 'access',
        templateUrl: '/static/frontend/views/access.html',
        redirectTo: 'home.access.accessIp',
        controller: 'AccessIpCtrl as vm',
        resolve: {
            authenticated: ['djangoAuth', function(djangoAuth){
                return djangoAuth.authenticationStatus();
            }],
        }
    })
    .state('home.access.accessIp', {
        url: '/access-IP',
        templateUrl: '/static/frontend/views/access_ip.html',
        controller: 'AccessIpCtrl as vm',
        resolve: {
            authenticated: ['djangoAuth', function(djangoAuth){
                return djangoAuth.authenticationStatus();
            }],
        }
    })
    .state('home.access.workarea', {
        url: '/workarea',
        templateUrl: '/static/frontend/views/access_workarea.html',
        controller: 'AccessWorkareaCtrl as vm',
        resolve: {
            authenticated: ['djangoAuth', function(djangoAuth){
                return djangoAuth.authenticationStatus();
            }],
        }
    })
    .state('home.access.createDip', {
        url: '/create-DIP',
        templateUrl: '/static/frontend/views/access_create_dip.html',
        controller: 'CreateDipCtrl as vm',
        params: {ip: null},
        resolve: {
            authenticated: ['djangoAuth', function(djangoAuth){
                return djangoAuth.authenticationStatus();
            }],
        }
    })
    .state('home.orders', {
        url: 'orders',
        templateUrl: '/static/frontend/views/orders.html',
        controller: 'OrdersCtrl as vm',
        resolve: {
            authenticated: ['djangoAuth', function(djangoAuth){
                return djangoAuth.authenticationStatus();
            }],
        }
    })
    .state('home.management', {
        url: 'management',
        templateUrl: '/static/frontend/views/management.html',
        controller: 'ManagementCtrl as vm',
        resolve: {
            authenticated: ['djangoAuth', function(djangoAuth){
                return djangoAuth.authenticationStatus();
            }],
        }
    })
    .state('home.appraisal', {
        url: 'appraisal',
        templateUrl: '/static/frontend/views/appraisal.html',
        controller: 'AppraisalCtrl as vm',
        params: {tag: null, ips: [], archive_policy: null},
        resolve: {
            authenticated: ['djangoAuth', function(djangoAuth){
                return djangoAuth.authenticationStatus();
            }],
        }
    })
    .state('home.administration', {
        url: 'administration',
        templateUrl: '/static/frontend/views/administration.html',
        controller: 'AdministrationCtrl as vm',
        redirectTo: 'home.administration.mediaInformation',
        resolve: {
            authenticated: ['djangoAuth', function(djangoAuth){
                return djangoAuth.authenticationStatus();
            }],
        }
    })
    .state('home.administration.mediaInformation', {
        url: '/media-information',
        templateUrl: '/static/frontend/views/administration_media_information.html',
        controller: 'MediaInformationCtrl as vm',
        resolve: {
            authenticated: ['djangoAuth', function(djangoAuth){
                return djangoAuth.authenticationStatus();
            }],
        }
    })
    .state('home.administration.robotInformation', {
        url: '/robot-information',
        templateUrl: '/static/frontend/views/administration_robot_information.html',
        controller: 'RobotInformationCtrl as vm',
        resolve: {
            authenticated: ['djangoAuth', function(djangoAuth){
                return djangoAuth.authenticationStatus();
            }],
        }
    })
    .state('home.administration.queues', {
        url: '/queues',
        templateUrl: 'static/frontend/views/administration_queues.html',
        controller: 'QueuesCtrl as vm',
        resolve: {
            authenticated: ['djangoAuth', function(djangoAuth){
                return djangoAuth.authenticationStatus();
            }],
        }
    })
    .state('home.administration.storageMigration', {
        url: '/storage-migration',
        templateUrl: 'static/frontend/views/administration_storage_migration.html',
        controller: 'StorageMigrationCtrl as vm',
        resolve: {
            authenticated: ['djangoAuth', function(djangoAuth){
                return djangoAuth.authenticationStatus();
            }],
        }
    })
    .state('home.administration.storageMaintenance', {
        url: '/storage-maintenance',
        templateUrl: 'static/frontend/views/administration_storage_maintenance.html',
        controller: 'StorageMaintenanceCtrl as vm',
        resolve: {
            authenticated: ['djangoAuth', function(djangoAuth){
                return djangoAuth.authenticationStatus();
            }],
        }
    })
    .state('restricted', {
        url: '/restricted',
        templateUrl: '/static/frontend/views/restricted.html',
        controller: 'RestrictedCtrl as vm',
        resolve: {
            authenticated: ['djangoAuth', function(djangoAuth){
                return djangoAuth.authenticationStatus();
            }],
        }
    })
    .state('authRequired', {
        url: '/auth-required',
        templateUrl: '/static/frontend/views/auth_required.html',
        controller: 'AuthRequiredCtrl as vm',
        resolve: {
            authenticated: ['djangoAuth', function(djangoAuth){
                return djangoAuth.authenticationStatus();
            }],
        }
    });
    $urlRouterProvider.otherwise('my-page');
})
.config(function($animateProvider) {
    // Only animate elements with the 'angular-animate' class
    $animateProvider.classNameFilter(/angular-animate|ui-select-/);
})
.config(['markedProvider', function (markedProvider) {
    function isURL(str) {
        var urlRegex = '^(?!mailto:)(?:(?:http|https|ftp)://)(?:\\S+(?::\\S*)?@)?(?:(?:(?:[1-9]\\d?|1\\d\\d|2[01]\\d|22[0-3])(?:\\.(?:1?\\d{1,2}|2[0-4]\\d|25[0-5])){2}(?:\\.(?:[0-9]\\d?|1\\d\\d|2[0-4]\\d|25[0-4]))|(?:(?:[a-z\\u00a1-\\uffff0-9]+-?)*[a-z\\u00a1-\\uffff0-9]+)(?:\\.(?:[a-z\\u00a1-\\uffff0-9]+-?)*[a-z\\u00a1-\\uffff0-9]+)*(?:\\.(?:[a-z\\u00a1-\\uffff]{2,})))|localhost)(?::\\d{2,5})?(?:(/|\\?|#)[^\\s]*)?$';
        var url = new RegExp(urlRegex, 'i');
        return str.length < 2083 && url.test(str);
    }
    markedProvider.setOptions({
        gfm: true,
        tables: true,
    });
    markedProvider.setRenderer({
        link: function(href, title, text) {
            if(!isURL(href)) {
                return "<a ng-click='scrollToLink(\"" + href + "\")'" + ">" + text + "</a>";
            } else {
                return "<a href='" + href + "'" + (title ? " title='" + title + "'" : '') + " target='_blank'>" + text + "</a>";
            }
        }
    });
}])
.config(['$httpProvider', function($httpProvider, $rootScope) {
    $httpProvider.defaults.xsrfCookieName = 'csrftoken';
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
    $httpProvider.interceptors.push(['$q', '$location', function ($q, $location) {
        return {
            'responseError': function(response) {
                if(response.status === 401 || response.status === 403) {
                    $location.assign('/');
                }
                return $q.reject(response);
            }
        };
    }]);
}])
.config(['$uibTooltipProvider', function($uibTooltipProvider) {
    var parser = new UAParser();
    var result = parser.getResult();
    var touch = result.device && (result.device.type === 'tablet' || result.device.type === 'mobile');
    if ( touch ){
        $uibTooltipProvider.options({trigger: 'dontTrigger'});
    } else {
        $uibTooltipProvider.options({trigger: 'mouseenter'});
    }
}])
.config(['$resourceProvider', function($resourceProvider) {
  // Don't strip trailing slashes from calculated URLs
  $resourceProvider.defaults.stripTrailingSlashes = false;
}])
.config(['$compileProvider', 'appConfig', '$logProvider', function ($compileProvider, appConfig, $logProvider) {
    $compileProvider.debugInfoEnabled(appConfig.debugInfo);
    $compileProvider.commentDirectivesEnabled(appConfig.commentDirectives);
    $compileProvider.cssClassDirectivesEnabled(appConfig.cssClassDirectives);
    $logProvider.debugEnabled(appConfig.logDebug);
}])
.config(function(stConfig) {
    stConfig.sort.delay = -1;
})
.config(function (formlyConfigProvider){
    function _defineProperty(obj, key, value) {
        if (key in obj) {
            Object.defineProperty(obj, key, {
                value: value,
                enumerable: true,
                configurable: true,
                writable: true
            });
        } else {
            obj[key] = value;
        }
        return obj;
    };
    formlyConfigProvider.setType({
        name: 'input',
        templateUrl: 'static/frontend/views/form_template_input.html',
        overwriteOk: true,
        wrapper: ['bootstrapHasError'],
        defaultOptions: function(options) {
            return {
                templateOptions: {
                    validation: {
                        show: true
                    }
                }
            };
        }
    });
    
    formlyConfigProvider.setType({
        name: 'select',
        templateUrl: 'static/frontend/views/form_template_select.html',
        overwriteOk: true,
        wrapper: ['bootstrapHasError'],
        defaultOptions: function defaultOptions(options) {
            var ngOptions = options.templateOptions.ngOptions || 'option[to.valueProp || \'value\'] as option[to.labelProp || \'name\'] group by option[to.groupProp || \'group\'] for option in to.options';
            return {
                templateOptions: {
                    validation: {
                        show: true
                    }
                },
                ngModelAttrs: _defineProperty({}, ngOptions, {
                    value: options.templateOptions.optionsAttr || 'ng-options'
                })
            };
        },
    });
    
    formlyConfigProvider.setType({
        name: 'datepicker',
        templateUrl: "static/frontend/views/datepicker_template.html",
        overwriteOk: true,
        wrapper: ['bootstrapHasError'],
        defaultOptions: function defaultOptions(options) {
            return {
                templateOptions: {
                    validation: {
                        show: true
                    }
                }
            };
        }
    });
    moment.locale('sv');

    formlyConfigProvider.setType({
        name: 'select-tree-edit',
        template: '<select class="form-control" ng-model="model[options.key]"><option value="" disabled hidden>Choose here</option></select>',
        wrapper: ['bootstrapLabel', 'bootstrapHasError'],
        defaultOptions: function defaultOptions(options) {
            /* jshint maxlen:195 */
            var ngOptions = options.templateOptions.ngOptions || "option[to.valueProp || 'value'] as option[to.labelProp || 'name'] group by option[to.groupProp || 'group'] for option in to.options";
            return {
                ngModelAttrs: _defineProperty({}, ngOptions, {
                    value: options.templateOptions.optionsAttr || 'ng-options'
                })
            };
        },
        
        apiCheck: function apiCheck(check) {
            return {
                templateOptions: {
                    label: check.string.optional,
                    options: check.arrayOf(check.object),
                    optionsAttr: check.string.optional,
                    labelProp: check.string.optional,
                    valueProp: check.string.optional,
                    groupProp: check.string.optional
                }
            };
        }
    });
    
    formlyConfigProvider.setWrapper({
        name: 'validation',
        types: ['input', 'datepicker', 'select'],
        templateUrl: 'static/frontend/views/form_error_messages.html'
    });
})
.directive('setTouched', function MainCtrl() {
    return {
        restrict: 'A', // only activate on element attribute
        require: '?ngModel', // get a hold of NgModelController
        link: function(scope, element, attrs, ngModel) {
            if (!ngModel) return; // do nothing if no ng-model
            element.on('blur', function() {
                var modelControllers = scope.$eval(attrs.setTouched);
                if(angular.isArray(modelControllers)) {
                    angular.forEach(modelControllers, function(modelCntrl) {
                        modelCntrl.$setTouched();
                    });
                }
            });
        }
    };
})
.run(function(djangoAuth, $rootScope, $state, $location, $window, $cookies, PermPermissionStore, PermRoleStore, $http, myService, formlyConfig, formlyValidationMessages){
    formlyConfig.extras.errorExistsAndShouldBeVisibleExpression = 'form.$submitted || fc.$touched || fc[0].$touched';
    formlyValidationMessages.addStringMessage('required', 'This field is required');
    
    djangoAuth.initialize('/rest-auth', false).then(function(response) {
        $rootScope.auth = response.data;
        $window.sessionStorage.setItem("view-type", response.data.ip_list_view_type);
        $rootScope.listViewColumns = myService.generateColumns(response.data.ip_list_columns).activeColumns;
        myService.getPermissions(response.data.permissions);

        $rootScope.$on('$stateChangeStart', function (event, toState, toParams, fromState) {
            if (toState.name === 'login') {
                return;
            }
            if (djangoAuth.authenticated !== true) {
                event.preventDefault();
                $state.go('login'); // go to login
            }

            // now, redirect only not authenticated
        });
    }).catch(function(status) {
        $state.go('login');
    });
    
    $rootScope.$on('$stateChangeStart', function(evt, to, params) {
        if (to.redirectTo) {
            evt.preventDefault();
            $state.go(to.redirectTo, params, {location: 'replace'})
        }
    });
});
