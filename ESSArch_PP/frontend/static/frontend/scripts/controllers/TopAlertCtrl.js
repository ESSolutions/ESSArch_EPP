angular.module('myApp').controller('TopAlertCtrl', function(appConfig, TopAlert, $timeout, $interval, $scope, $rootScope, $http, $window) {
    var vm = this;
    vm.visible = false;
    vm.alerts = [];
    vm.frontendAlerts = [];
    vm.backendAlerts = [];
    var interval;
    var updateInterval;
    vm.$onInit = function () {
        Messenger.options = {
            extraClasses: 'messenger-fixed messenger-on-bottom messenger-on-right',
            theme: 'flat'
        }
        vm.updateUnseen();
        if(!$rootScope.useWebsocket) {
            interval = $interval(function() {
                vm.getNotifications();
                vm.updateUnseen();
            }, appConfig.notificationInterval)
        }
    }

    $scope.$watch(function () { return $rootScope.useWebsocket }, function (newValue, oldValue) {
        if (newValue != oldValue) {
            if ($rootScope.useWebsocket) {
                $interval.cancel(interval);
            } else {
                interval = $interval(function () {
                    vm.getNotifications();
                    vm.updateUnseen();
                }, appConfig.notificationInterval)
            }
        }
    })

    vm.getNotifications = function(show) {
        if(angular.isUndefined(show)) {
            show = true;
        }
        vm.nextPageLoading = true;
        var pageSize = Math.ceil(($(window).height() * 0.6) / 38)+2;
        return TopAlert.getNotifications(pageSize).then(function(data) {
            vm.nextPageLoading = false;
            vm.backendAlerts = data;
            vm.alerts = vm.backendAlerts;
            return vm.alerts;
        });
    }

    vm.updateUnseen = function(count) {
        if(count) {
            $rootScope.unseenNotifications = count;
        } else {
            $http.head(appConfig.djangoUrl + "notifications/", {params: { seen: false }}).then(function(response) {
                $rootScope.unseenNotifications = response.headers().count;
            });
        }
    }

    vm.showAlert = function() {
        vm.visible = true;
        vm.getNotifications();
    }

    vm.setSeen = function(alerts) {
        alerts.forEach(function(alert) {
            if(alert.id && !alert.seen) {
                $http({
                    method: 'PATCH',
                    url: appConfig.djangoUrl + 'notifications/' + alert.id + '/',
                    data: { seen: true }
                }).then(function(response) {
                    alert.seen = true;
                    if($rootScope.unseenNotifications > 0) {
                        $rootScope.unseenNotifications -= 1;
                    }
                }).catch(function(response) {});
            } else if(!alert.id) {
                alert.seen = true;
            }
        });
    }

    vm.hideAlert = function() {
        vm.visible = false;
        $window.onclick = null;
    }

    vm.removeAlert = function (alert, index) {
        TopAlert.delete(alert.id).then(function (response) {
            vm.backendAlerts.splice(index, 1);
            vm.alerts.splice(index, 1);
        });
    }

    function getNext() {
        return TopAlert.getNextNotification().then(function(data) {
            vm.backendAlerts.push(data[0]);
            vm.alerts = vm.backendAlerts;
            if(!vm.alerts.length == 0) {
                vm.visible = false;
            }
            return vm.alerts;
        }).catch(function(response) {
            if(!vm.alerts.length == 0) {
                vm.visible = false;
            }
            return vm.alerts;
        })
    }
    vm.clearAll = function() {
        TopAlert.deleteAll().then(function(response) {
            vm.visible = false;
            vm.alerts = [];
            vm.backendAlerts = [];
            vm.frontendAlerts = [];
            vm.updateUnseen();
        })
    }
    vm.nextPage = function () {
        if(!vm.nextPageLoading) {
            vm.nextPageLoading = true;
            TopAlert.getNextPage(10, vm.alerts[vm.alerts.length-1].id).then(function(response) {
                vm.nextPageLoading = false;
                response.data.forEach(function(x) {
                    vm.backendAlerts.push(x);
                });
                vm.alerts = vm.backendAlerts;
            })
        }
    }

    /**
     * Show top alert
     * @param message - Message to show on the the alert
     * @param level - level of alert, applies a class to the alert
     * @param time - Adds a duration to the alert
     */

    vm.addAlert = function (id, message, level, time, seen, options) {
        var timer = null;
        var alert = {message: message, level: level, time_created: new Date(), seen: false, options: options};
        if(id) {
            alert.id = id;
            alert.seen = seen
            vm.backendAlerts.unshift(alert);
        } else {
            vm.frontendAlerts.unshift(alert);
        }
        Messenger().post({
            message: message,
            type: level,
            hideAfter: time?time/1000:10,
            showCloseButton: true
        });
    }

    // Listen for show/hide events
    $scope.$on('add_top_alert', function (event, data) {
        vm.addAlert(data.id, data.message, data.level, data.time, true, data.options);
    });
    $scope.$on('add_unseen_top_alert', function (event, data) {
        vm.updateUnseen(data.count);
        vm.addAlert(data.id, data.message, data.level, data.time, false);
        if(vm.showAlerts) {
            vm.setSeen(vm.alerts.slice(0,5));
        }
    });
    $scope.$on('show_top_alert', function (event, data) {
        if(vm.alerts.length > 0) {
            vm.showAlert();
            $timeout(function() {
                vm.showAlerts = true;
                vm.setSeen(vm.alerts.slice(0, 5));
            }, 300);
        }
    });
    $scope.$on('toggle_top_alert', function (event, data) {
        if(vm.visible) {
            vm.hideAlert();
        } else {
            vm.showAlert();
            vm.setSeen(vm.alerts.slice(0, 5));
            $window.onclick = function(event) {
                var clickedElement = $(event.target);
                if (!clickedElement) return;
                var elementClasses = event.target.classList;
                var clickedOnAlertIcon = elementClasses.contains('fa-bell') ||
                elementClasses.contains('top-alert-container') ||
                elementClasses.contains('top-alert-container') ||
                clickedElement.parents('.top-alert-container').length
                if (!clickedOnAlertIcon) {
                    vm.hideAlert();
                    $scope.$apply();
                }
            }
        }
    });
    $scope.$on('hide_top_alert', function (event, data) {
        vm.hideAlert();
    });
    $scope.$on('get_top_alerts', function (event, data) {
        vm.getNotifications();
    });
});
