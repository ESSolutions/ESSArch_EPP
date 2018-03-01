angular.module('myApp').controller('TopAlertCtrl', function(appConfig, TopAlert, $timeout, $interval, $scope, $rootScope, $http) {
    var vm = this;
    vm.visible = false;
    vm.alerts = [];
    vm.frontendAlerts = [];
    vm.backendAlerts = [];
    vm.showAlerts = false;
    var interval;
    var updateInterval;
    vm.$onInit = function () {
        vm.getNotifications(false);
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
        return TopAlert.getNotifications().then(function(data) {
            vm.backendAlerts = data;
            vm.alerts = vm.frontendAlerts.concat(vm.backendAlerts).sort(function(a, b) {
                return new Date(b.time_created) - new Date(a.time_created);
            })
            if(vm.alerts.length > 0 && !vm.alerts[0].seen && show) {
                vm.showAlert();
            }
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
        if(vm.alerts.length >0) {
            vm.visible = true;
        }
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
        vm.showAlerts = false;
    }

    vm.removeAlert = function (alert) {
        if (alert.id) {
            TopAlert.delete(alert.id).then(function (response) {
                vm.backendAlerts.splice(vm.backendAlerts.indexOf(alert), 1);
                vm.alerts.splice(vm.alerts.indexOf(alert), 1);
                if (vm.alerts.length == 0) {
                    vm.updateUnseen(0);
                }
                if (vm.alerts.length == 0 && vm.showAlerts) {
                    vm.showAlerts = false;
                } else {
                if(vm.alerts.length < 7) {
                    getNext();
                }
                    vm.setSeen(vm.alerts.slice(0,5))
                }
            });
        } else {
            vm.frontendAlerts.splice(vm.frontendAlerts.indexOf(alert), 1);
            vm.alerts.splice(vm.alerts.indexOf(alert), 1);
            if (vm.alerts.length == 0 && vm.showAlerts) {
                vm.showAlerts = false;
            } else {
                if(vm.alerts.length < 7) {
                    getNext();
                }
                vm.setSeen(vm.alerts.slice(0,5))
            }
        }
    }

    function getNext() {
        return TopAlert.getNextNotification().then(function(data) {
            vm.backendAlerts.push(data[0]);
            vm.alerts = vm.frontendAlerts.concat(vm.backendAlerts).sort(function(a, b) {
                return new Date(b.time_created) - new Date(a.time_created);
            });
            if(!vm.showAlerts) {
                vm.visible = false;
            }
            return vm.alerts;
        }).catch(function(response) {
            if(!vm.showAlerts) {
                vm.visible = false;
            }
            return vm.alerts;
        })
    }
    vm.clearAll = function() {
        TopAlert.deleteAll().then(function(response) {
            vm.visible = false;
            vm.showAlerts = false;
            vm.alerts = [];
            vm.backendAlerts = [];
            vm.frontendAlerts = [];
            vm.updateUnseen();
        })
    }

    vm.toggleAlerts = function() {
        if(vm.alerts.length > 0) {
            vm.showAlerts = !vm.showAlerts;
            if(vm.showAlerts) {
                vm.setSeen(vm.alerts.slice(0, 5));
            }
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
        if (time) {
            timer = vm.setTimer(alert, time);
        } else {
            timer = vm.setTimer(alert, 5000);
        }
        vm.alerts = vm.frontendAlerts.concat(vm.backendAlerts).sort(function(a, b) {
            return new Date(b.time_created) - new Date(a.time_created);
        });
        vm.showAlert();
    }

    /**
     * Set timer for alert
     * @param time - Timer duration
     */
    vm.setTimer = function (alert, time) {
        return $timeout(function () {
            if (vm.visible && !vm.showAlerts && vm.alerts[0] == alert) {
                vm.hideAlert();
            }
            if(vm.showAlerts) {
                vm.setSeen(vm.alerts.slice(0,5));
            }
        }, time)
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
    $scope.$on('hide_top_alert', function (event, data) {
        vm.hideAlert();
    });
    $scope.$on('get_top_alerts', function (event, data) {
        vm.getNotifications();
    });
});
