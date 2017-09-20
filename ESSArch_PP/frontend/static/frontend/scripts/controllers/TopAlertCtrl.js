angular.module('myApp').controller('TopAlertCtrl', function(appConfig, TopAlert, $timeout, $interval, $scope, $rootScope, $http) {
    var vm = this;
    vm.visible = false;
    vm.alerts = [];
    vm.frontendAlerts = [];
    vm.backendAlerts = [];
    vm.showAlerts = false;
    var updateInterval;
    vm.$onInit = function() {
        $interval.cancel(updateInterval);
        updateInterval = $interval(function() {
            TopAlert.getNotifications().then(function(data) {
                vm.backendAlerts = data;
                vm.alerts = vm.frontendAlerts.concat(vm.backendAlerts).sort(function(a, b) {
                    return new Date(b.time_created) - new Date(a.time_created);
                })
                if(data.length > 0 && !data[0].seen) {
                    vm.showAlert();
                }
            });
        }, appConfig.notificationInterval);
    }

    $rootScope.getUnseen = function() {
        var unseen = 0;
        vm.alerts.forEach(function(alert) {
            if(!alert.seen) {
                unseen += 1;
            }
        })
        return unseen;
    }

    vm.showAlert = function() {
        vm.visible = true;
        vm.setSeen([vm.alerts[0]]);
    }

    vm.setSeen = function(alerts) {
        alerts.forEach(function(alert) {
            if(alert.id && !alert.seen) {
                $http({
                    method: 'PATCH',
                    url: appConfig.djangoUrl + 'notifications/' + alert.id + '/',
                    data: { seen: true }
                });
            } else if(!alert.id) {
                alert.seen = true;
            }
        });
    }

    vm.hideAlert = function() {
        vm.visible = false;
        vm.showAlerts = false;
    }

    vm.removeAlert = function (alert) {
        if (alert.id) {
            TopAlert.delete(alert.id).then(function (response) {
                vm.backendAlerts.splice(vm.backendAlerts.indexOf(alert), 1);
                vm.alerts.splice(vm.alerts.indexOf(alert), 1);
                if (vm.alerts.length == 0) {
                    vm.showAlerts = false;
                } else {
                    vm.setSeen(vm.alerts.slice(0,5))
                }
            });
        } else {
            vm.frontendAlerts.splice(vm.frontendAlerts.indexOf(alert), 1);
            vm.alerts.splice(vm.alerts.indexOf(alert), 1);
            if (vm.alerts.length == 0) {
                vm.showAlerts = false;
            }
        }
    }

    vm.clearAll = function() {
        vm.alerts.forEach(function(alert) {
            vm.removeAlert(alert);
        })
    }

    vm.toggleAlerts = function() {
        if(vm.alerts.length > 0) {
            vm.showAlerts = !vm.showAlerts;
        }
        if(vm.showAlerts) {
            vm.setSeen(vm.alerts.slice(0, 5));
        }
    }

    /**
     * Show top alert
     * @param message - Message to show on the the alert
     * @param level - level of alert, applies a class to the alert
     * @param time - Adds a duration to the alert
     */

    vm.addAlert = function (message, level, time) {
        var timer = null;
        var alert = {message: message, level: level, time_created: new Date(), seen: true};
        vm.frontendAlerts.unshift(alert);
        if (time) {
            timer = vm.setTimer(alert, time);
        }
        vm.showAlert();
    }

    /**
     * Set timer for alert
     * @param time - Timer duration
     */
    vm.setTimer = function (alert, time) {
        return $timeout(function () {
            vm.removeAlert(alert);
            vm.setSeen(vm.alerts.slice(0, 5));
        }, time)
    }

    // Listen for show/hide events
    $rootScope.$on('add_top_alert', function (event, data) {
        vm.addAlert(data.message, data.level, data.time);
    });
    $rootScope.$on('show_top_alert', function (event, data) {
        vm.showAlert();
        $timeout(function() {
            vm.showAlerts = true;
        }, 300);
    });
    $rootScope.$on('hide_top_alert', function (event, data) {
        vm.hideAlert();
    });

}).factory('TopAlert', function ($rootScope, appConfig, $http) {
    return {
        /**
         * Add top alert and show it
         * @param message - Message to show on the the alert
         * @param level - level of alert, applies a class to the alert
         * @param time - Adds a duration to the alert
         */
        add: function(message, level, time) {
            $rootScope.$broadcast('add_top_alert', { message: message, level: level, time: time });
        },
        /**
         * Show alert
         */
        show: function() {
            $rootScope.$broadcast('show_top_alert', {});
        },
        /**
         * Hide top alert
         */
        hide: function() {
            $rootScope.$broadcast('hide_top_alert', {});

        },
        getNotifications: function() {
            return $http.get(appConfig.djangoUrl + "notifications/", {params: {pager: "none"}}).then(function(response) {
                return response.data;
            })
        },
        delete: function(id) {
            return $http.delete(appConfig.djangoUrl + "notifications/" + id + "/").then(function(response) {
                return response;
            })
        },
        getUnseen: function() {
            if($rootScope.getUnseen) {
                return $rootScope.getUnseen();
            } else {
                return 0;
            }
        }
    }
});
