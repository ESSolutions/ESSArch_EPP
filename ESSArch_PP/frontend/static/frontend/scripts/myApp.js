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

Object.resolve = function(path, obj) {
    return path.split('.').reduce(function(prev, curr) {
        return prev ? prev[curr] : undefined
    }, obj || self)
}

function nestedPermissions(page) {
    // If page is an array it means that page is the field _permissions
    if(Array.isArray(page)) {
        return page;
    } else if(typeof(page) == "object") {
        var temp = [];
        for(var entry in page) {
            // Recursively build permission list
            temp = temp.concat(nestedPermissions(page[entry]));
        }
        return temp;
    }
}

/**
 * Check if state has a sub state that requires no permissions
 * @param {*} page
 */
function nestedEmptyPermissions(page) {
    if(Array.isArray(page)) {
        return page.length == 0;
    } else if(typeof(page) == "object") {
        for(var entry in page) {
            if(nestedEmptyPermissions(page[entry])) {
                return true;
            }
        }
        return false;
    }
}

angular.module('myApp', ['templates', 'ngRoute', 'treeControl', 'ui.bootstrap', 'formly', 'formlyBootstrap', 'smart-table', 'treeGrid', 'ui.router', 'ngCookies', 'permission', 'permission.ui', 'pascalprecht.translate', 'ngSanitize', 'ui.bootstrap.contextMenu', 'ui.select', 'flow', 'ui.bootstrap.datetimepicker', 'ui.dateTimeInput', 'ngAnimate', 'ngMessages', 'myApp.config', 'permission.config', 'ig.linkHeaderParser', 'hc.marked', 'ngFilesizeFilter', 'angular-clipboard', "ngResource", 'relativeDate', 'ngWebSocket', 'ngJsTree', 'angular-cron-jobs', 'angularResizable'])
.config(function($routeProvider, formlyConfigProvider, $urlMatcherFactoryProvider, $stateProvider, $urlRouterProvider, $rootScopeProvider, $uibTooltipProvider, permissionConfig) {

    $urlMatcherFactoryProvider.strictMode(false);

    $stateProvider
    .state('home', {
        url: '/',
        templateUrl: '/static/frontend/views/home.html',
    })
    .state('login', {
        url: '/login',
        params: {
            requestedPage: '/login',
        },
        templateUrl: 'login.html',
        controller: 'LoginCtrl as vm',
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
    .state('home.info', {
        url: 'info',
        templateUrl: '/static/frontend/views/my_page.html',
        controller: 'MyPageCtrl as vm',
        resolve: {
            authenticated: ['djangoAuth', function(djangoAuth){
                return djangoAuth.authenticationStatus();
            }],
        }
    })
    .state('home.access.search', {
        url: '/search?{query:json}',
        templateUrl: '/static/frontend/views/search.html',
        controller: 'SearchCtrl as vm',
        resolve: {
            authenticated: ['djangoAuth', function(djangoAuth){
                return djangoAuth.authenticationStatus();
            }],
        },
        data: {
            permissions: {
                only: nestedPermissions(Object.resolve("home.access.search", permissionConfig)),
                redirectTo: 'home.restricted'
            }
        },
    })
    .state('home.access.search.classificationStructures', {
        url: '/classification-structures',
        template: '<classification-structure-editor></classification-structure-editor>',
        resolve: {
            authenticated: ['djangoAuth', function(djangoAuth){
                return djangoAuth.authenticationStatus();
            }],
        },
        data: {
            permissions: {
                only: nestedPermissions(Object.resolve("home.access.search", permissionConfig)),
                redirectTo: 'home.restricted'
            }
        },
    })
    .state('home.access.search.archiveManager', {
        url: '/archive-manager',
        template: '<archive-manager></archive-manager>',
        resolve: {
            authenticated: ['djangoAuth', function(djangoAuth){
                return djangoAuth.authenticationStatus();
            }],
        },
        data: {
            permissions: {
                only: nestedPermissions(Object.resolve("home.access.search", permissionConfig)),
                redirectTo: 'home.restricted'
            }
        },
    })
    .state('home.access.search.information_package', {
        url: '/information_package/:id',
        templateUrl: '/static/frontend/views/search_ip_detail.html',
        controller: 'SearchIpCtrl as vm',
        resolve: {
            authenticated: ['djangoAuth', function(djangoAuth){
                return djangoAuth.authenticationStatus();
            }],
        },
        data: {
            permissions: {
                only: nestedPermissions(Object.resolve("home.access.search", permissionConfig)),
                redirectTo: 'home.restricted'
            }
        },
    })
    .state('home.access.search.component', {
        url: '/component/:id',
        templateUrl: '/static/frontend/views/search_detail.html',
        controller: 'SearchDetailCtrl as vm',
        resolve: {
            authenticated: ['djangoAuth', function(djangoAuth){
                return djangoAuth.authenticationStatus();
            }],
        },
        data: {
            permissions: {
                only: nestedPermissions(Object.resolve("home.access.search", permissionConfig)),
                redirectTo: 'home.restricted'
            }
        },
    })
    .state('home.access.search.directory', {
        url: '/directory/:id',
        templateUrl: '/static/frontend/views/search_detail.html',
        controller: 'SearchDetailCtrl as vm',
        resolve: {
            authenticated: ['djangoAuth', function(djangoAuth){
                return djangoAuth.authenticationStatus();
            }],
        },
        data: {
            permissions: {
                only: nestedPermissions(Object.resolve("home.access.search", permissionConfig)),
                redirectTo: 'home.restricted'
            }
        },
    })
    .state('home.access.search.document', {
        url: '/document/:id',
        templateUrl: '/static/frontend/views/search_detail.html',
        controller: 'SearchDetailCtrl as vm',
        resolve: {
            authenticated: ['djangoAuth', function(djangoAuth){
                return djangoAuth.authenticationStatus();
            }],
        },
        data: {
            permissions: {
                only: nestedPermissions(Object.resolve("home.access.search", permissionConfig)),
                redirectTo: 'home.restricted'
            }
        },
    })
    .state('home.access.search.archive', {
        url: '/archive/:id',
        templateUrl: '/static/frontend/views/search_detail.html',
        controller: 'SearchDetailCtrl as vm',
        resolve: {
            authenticated: ['djangoAuth', function(djangoAuth){
                return djangoAuth.authenticationStatus();
            }],
        },
        data: {
            permissions: {
                only: nestedPermissions(Object.resolve("home.access.search", permissionConfig)),
                redirectTo: 'home.restricted'
            }
        },
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
    .state('home.ingest', {
        url: 'ingest',
        templateUrl: '/static/frontend/views/ingest.html',
        controller: 'IngestCtrl as vm',
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
            authenticated: ['djangoAuth',  function(djangoAuth){
                return djangoAuth.authenticationStatus();
            }],
        },
        data: {
            permissions: {
                only: nestedPermissions(Object.resolve("home.ingest.reception", permissionConfig)),
                redirectTo: 'home.restricted'
            }
        },
    })
    .state('home.ingest.ipApproval', {
        url: '/approval',
        templateUrl: '/static/frontend/views/ip_approval.html',
        controller: 'IpApprovalCtrl as vm',
        resolve: {
            authenticated: ['djangoAuth', function(djangoAuth){
                return djangoAuth.authenticationStatus();
            }],
        },
        data: {
            permissions: {
                only: nestedPermissions(Object.resolve("home.ingest.ipApproval", permissionConfig)),
                redirectTo: 'home.restricted'
            }
        },
    })
    .state('home.ingest.workarea', {
        url: '/workarea',
        templateUrl: '/static/frontend/views/ingest_workarea.html',
        controller: 'IngestWorkareaCtrl as vm',
        resolve: {
            authenticated: ['djangoAuth', function(djangoAuth){
                return djangoAuth.authenticationStatus();
            }],
        },
        data: {
            permissions: {
                only: nestedPermissions(Object.resolve("home.ingest.workarea", permissionConfig)),
                redirectTo: 'home.restricted'
            }
        },
    })
    .state('home.access', {
        url: 'access',
        templateUrl: '/static/frontend/views/access.html',
        controller: 'AccessCtrl as vm',
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
        },
        data: {
            permissions: {
                only: nestedPermissions(Object.resolve("home.access.accessIp", permissionConfig)),
                redirectTo: 'home.restricted'
            }
        },
    })
    .state('home.access.workarea', {
        url: '/workarea',
        templateUrl: '/static/frontend/views/access_workarea.html',
        controller: 'AccessWorkareaCtrl as vm',
        resolve: {
            authenticated: ['djangoAuth', function(djangoAuth){
                return djangoAuth.authenticationStatus();
            }],
        },
        data: {
            permissions: {
                only: nestedPermissions(Object.resolve("home.access.workarea", permissionConfig)),
                redirectTo: 'home.restricted'
            }
        },
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
        },
        data: {
            permissions: {
                only: nestedPermissions(Object.resolve("home.access.createDip", permissionConfig)),
                redirectTo: 'home.restricted'
            }
        },
    })
    .state('home.access.orders', {
        url: '/orders',
        templateUrl: '/static/frontend/views/orders.html',
        controller: 'OrdersCtrl as vm',
        resolve: {
            authenticated: ['djangoAuth', function(djangoAuth){
                return djangoAuth.authenticationStatus();
            }],
        },
        data: {
            permissions: {
                only: nestedPermissions(Object.resolve("home.orders", permissionConfig)),
                redirectTo: 'home.restricted'
            }
        },
    })
    .state('home.management', {
        url: 'management',
        templateUrl: '/static/frontend/views/management.html',
        controller: 'ManagementCtrl as vm',
        resolve: {
            authenticated: ['djangoAuth', function(djangoAuth){
                return djangoAuth.authenticationStatus();
            }],
        },
        data: {
            permissions: {
                only: nestedPermissions(Object.resolve("home.management", permissionConfig)),
                redirectTo: 'home.restricted'
            }
        },
    })
    .state('home.archiveMaintenance', {
        url: 'archive-maintenance',
        templateUrl: '/static/frontend/views/archive_maintenance.html',
        resolve: {
            authenticated: ['djangoAuth', function(djangoAuth){
                return djangoAuth.authenticationStatus();
            }],
        }
    })
    .state('home.archiveMaintenance.start', {
        url: '/start',
        templateUrl: '/static/frontend/views/archive_maintenance_start.html',
        controller: 'AppraisalCtrl as vm',
        resolve: {
            authenticated: ['djangoAuth', function(djangoAuth){
                return djangoAuth.authenticationStatus();
            }],
        },
        data: {
            permissions: {
                only: nestedPermissions(Object.resolve("home.archiveMaintenance.start", permissionConfig)),
                redirectTo: 'home.restricted'
            }
        },
    })
    .state('home.archiveMaintenance.appraisal', {
        url: '/appraisal',
        templateUrl: '/static/frontend/views/appraisal.html',
        controller: 'AppraisalCtrl as vm',
        resolve: {
            authenticated: ['djangoAuth', function(djangoAuth){
                return djangoAuth.authenticationStatus();
            }],
        },
        data: {
            permissions: {
                only: nestedPermissions(Object.resolve("home.archiveMaintenance.appraisal", permissionConfig)),
                redirectTo: 'home.restricted'
            }
        },
    })
    .state('home.archiveMaintenance.conversion', {
        url: '/conversion',
        templateUrl: '/static/frontend/views/conversion.html',
        controller: 'ConversionCtrl as vm',
        resolve: {
            authenticated: ['djangoAuth', function(djangoAuth){
                return djangoAuth.authenticationStatus();
            }],
        },
        data: {
            permissions: {
                only: nestedPermissions(Object.resolve("home.archiveMaintenance.appraisal", permissionConfig)),
                redirectTo: 'home.restricted'
            }
        },
    })
    .state('home.administration', {
        url: 'administration',
        templateUrl: '/static/frontend/views/administration.html',
        controller: 'AdministrationCtrl as vm',
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
        },
        data: {
            permissions: {
                only: nestedPermissions(Object.resolve("home.administration.mediaInformation", permissionConfig)),
                redirectTo: 'home.restricted'
            }
        },
    })
    .state('home.administration.robotInformation', {
        url: '/robot-information',
        templateUrl: '/static/frontend/views/administration_robot_information.html',
        controller: 'RobotInformationCtrl as vm',
        resolve: {
            authenticated: ['djangoAuth', function(djangoAuth){
                return djangoAuth.authenticationStatus();
            }],
        },
        data: {
            permissions: {
                only: nestedPermissions(Object.resolve("home.administration.robotInformation", permissionConfig)),
                redirectTo: 'home.restricted'
            }
        },
    })
    .state('home.administration.queues', {
        url: '/queues',
        templateUrl: 'static/frontend/views/administration_queues.html',
        controller: 'QueuesCtrl as vm',
        resolve: {
            authenticated: ['djangoAuth', function(djangoAuth){
                return djangoAuth.authenticationStatus();
            }],
        },
        data: {
            permissions: {
                only: nestedPermissions(Object.resolve("home.administration.queues", permissionConfig)),
                redirectTo: 'home.restricted'
            }
        },
    })
    .state('home.administration.storageMigration', {
        url: '/storage-migration',
        templateUrl: 'static/frontend/views/administration_storage_migration.html',
        controller: 'StorageMigrationCtrl as vm',
        resolve: {
            authenticated: ['djangoAuth', function(djangoAuth){
                return djangoAuth.authenticationStatus();
            }],
        },
        data: {
            permissions: {
                only: nestedPermissions(Object.resolve("home.administration.storageMigration", permissionConfig)),
                redirectTo: 'home.restricted'
            }
        },
    })
    .state('home.administration.storageMaintenance', {
        url: '/storage-maintenance',
        templateUrl: 'static/frontend/views/administration_storage_maintenance.html',
        controller: 'StorageMaintenanceCtrl as vm',
        resolve: {
            authenticated: ['djangoAuth', function(djangoAuth){
                return djangoAuth.authenticationStatus();
            }],
        },
        data: {
            permissions: {
                only: nestedPermissions(Object.resolve("home.administration.storageMaintenance", permissionConfig)),
                redirectTo: 'home.restricted'
            }
        },
    })
    .state('home.administration.profileManager', {
        url: '/profile-manager',
        templateUrl: 'static/frontend/views/profile_manager.html',
        controller: 'ProfileManagerCtrl as vm',
        resolve: {
            authenticated: ['djangoAuth', function(djangoAuth){
                return djangoAuth.authenticationStatus();
            }],
        },
        data: {
            permissions: {
                only: nestedPermissions(Object.resolve("home.administration.profileManager", permissionConfig)),
                redirectTo: 'home.restricted'
            }
        },
    })
    .state('home.administration.profileManager.saEditor', {
        url: '/sa-editor',
        template: '<sa-editor></sa-editor>',
        resolve: {
            authenticated: ['djangoAuth', function(djangoAuth){
                return djangoAuth.authenticationStatus();
            }],
        },
        data: {
            permissions: {
                only: nestedPermissions(Object.resolve("home.administration.profileManager.saEditor", permissionConfig)),
                redirectTo: 'home.restricted'
            }
        },
    })
    .state('home.administration.profileManager.profileMaker', {
        url: '/profile-maker',
        template: '<profile-maker></profile-maker>',
        resolve: {
            authenticated: ['djangoAuth', function(djangoAuth){
                return djangoAuth.authenticationStatus();
            }],
        },
        data: {
            permissions: {
                only: nestedPermissions(Object.resolve("home.administration.profileManager.profileMaker", permissionConfig)),
                redirectTo: 'home.restricted'
            }
        },
    })
    .state('home.administration.profileManager.import', {
        url: '/import',
        template: '<import></import>',
        resolve: {
            authenticated: ['djangoAuth', function(djangoAuth){
                return djangoAuth.authenticationStatus();
            }],
        },
        data: {
            permissions: {
                only: nestedPermissions(Object.resolve("home.administration.profileManager.import", permissionConfig)),
                redirectTo: 'home.restricted'
            }
        },
    })
    .state('home.administration.profileManager.export', {
        url: '/export',
        template: '<export></export>',
        resolve: {
            authenticated: ['djangoAuth', function(djangoAuth){
                return djangoAuth.authenticationStatus();
            }],
        },
        data: {
            permissions: {
                only: nestedPermissions(Object.resolve("home.administration.profileManager.export", permissionConfig)),
                redirectTo: 'home.restricted'
            }
        },
    })
    .state('home.restricted', {
        url: 'restricted',
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
    $urlRouterProvider.otherwise( function($injector) {
        var $state = $injector.get("$state");
        $state.go('home.info');
    });

    $urlRouterProvider.deferIntercept();
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
.config(['$httpProvider', '$windowProvider', function($httpProvider, $windowProvider) {
    var $window = $windowProvider.$get();
    $httpProvider.defaults.xsrfCookieName = 'csrftoken';
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
    $httpProvider.interceptors.push(['$q', '$location', '$rootScope', function ($q, $location, $rootScope) {
        return {
            'response': function(response) {
                if($rootScope.disconnected) {
                    $rootScope.disconnected = false;
                    $rootScope.$broadcast("reconnected", {detail: "Connection has been restored"});
                }
                return response;
            },
            'responseError': function(response) {
                if(response.status == 500) {
                    var msg = "Internal server error";
                    if(response.data.detail) {
                        msg = response.data.detail;
                    }
                    $rootScope.$broadcast('add_notification', { message: msg, level: "error", time: null});
                }
                if(response.status === 503) {
                    var msg = "Request failed, try again";
                    if(response.data.detail) {
                        msg = response.data.detail;
                    }
                    $rootScope.$broadcast('add_notification', { message: msg, level: "error", time: null});
                }
                if((response.status === 401 || response.status === 403) && !response.config.noAuth) {
                    if ($location.path() != '/login' && $location.path() != ''){
                        $window.location.assign('/');
                    }
                }
                if(response.status <= 0) {
                    $rootScope.$broadcast("disconnected", {detail: "Lost connection to server"});
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
.config(function ($permissionProvider) {
    $permissionProvider.suppressUndefinedPermissionWarning(true);
})
.config(function(stConfig) {
    stConfig.sort.delay = -1;
})
.config(['$compileProvider', function ($compileProvider) {
    $compileProvider.aHrefSanitizationWhitelist(/^\s*(https?|ftp|mailto|tel|file|blob|data):/);
}])
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
.run(function(djangoAuth, $rootScope, $state, $location, $window, $cookies, $timeout, PermPermissionStore, PermRoleStore, $http, myService, formlyConfig, formlyValidationMessages, $urlRouter, permissionConfig, Messenger){
    formlyConfig.extras.errorExistsAndShouldBeVisibleExpression = 'form.$submitted || fc.$touched || fc[0].$touched';
    formlyValidationMessages.addStringMessage('required', 'This field is required');
    $rootScope.app = 'ESSArch Preservation Platform'
    $rootScope.flowObjects = {};
    djangoAuth.initialize('/rest-auth', false).then(function(response) {
        $rootScope.auth = response.data;
        myService.getPermissions(response.data.permissions);
        // kick-off router and start the application rendering
        $urlRouter.sync();
        // Also enable router to listen to url changes
        $urlRouter.listen();
        $rootScope.listViewColumns = myService.generateColumns(response.data.ip_list_columns).activeColumns;
        $rootScope.$on('$stateChangeStart', function (event, toState, toParams, fromState) {
            if (toState.name === 'login') {
                return;
            }
            if (djangoAuth.authenticated !== true) {
                console.log('Not authenticated, redirecting to login');
                event.preventDefault();
                $state.go('login'); // go to login
            }
        });
    }).catch(function(status) {
        console.log('Got error response from auth api, redirecting to login with requested page:', $location.path());
        $state.go('login', {requestedPage: $location.path()});
    });

    $rootScope.$on('$stateChangeStart', function(evt, to, params, from) {
        if (to.redirectTo) {
            evt.preventDefault();
            $state.go(to.redirectTo, params, {location: 'replace'})
        }

        if(to.name == 'login' && djangoAuth.authenticated) {
            evt.preventDefault();
            if(from.name != "") {
                $state.transitionTo(from.name);
            } else {
                $state.transitionTo('home.info');
            }
        }

        if(to.name == "home.ingest" || to.name == "home.access" || to.name == "home.administration" || to.name == "home.administration.profileManager" || to.name == "home.archiveMaintenance") {
            evt.preventDefault();
            var resolved = Object.resolve(to.name, permissionConfig);
            for( var key in resolved) {
                if(key != "_permissions" && myService.checkPermissions(nestedPermissions(resolved[key]))) {
                    $state.go(to.name + "." + key);
                    return;
                }
            }
            $state.go("home.restricted");
            return;
        }

    });
});
