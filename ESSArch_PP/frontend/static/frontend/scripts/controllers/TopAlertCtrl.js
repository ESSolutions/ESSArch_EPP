angular.module('myApp').controller('TopAlertCtrl', function(appConfig, TopAlert, $timeout, $interval, $scope, $rootScope, $http) {
    var vm = this;
    vm.visible = false;
    vm.alerts = [];
    vm.frontendAlerts = [];
    vm.backendAlerts = [];
    vm.showAlerts = false;
    var updateInterval;
    vm.$onInit = function () {
        vm.getNotifications();
        vm.updateUnseen();
    }

    vm.getNotifications = function() {
        return TopAlert.getNotifications().then(function(data) {
            vm.backendAlerts = data;
            vm.alerts = vm.frontendAlerts.concat(vm.backendAlerts).sort(function(a, b) {
                return new Date(b.time_created) - new Date(a.time_created);
            })
            if(vm.alerts.length > 0 && !vm.alerts[0].seen) {
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
            vm.setSeen([vm.alerts[0]]);
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
                    $rootScope.unseenNotifications -= 1;
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
            if (vm.alerts.length == 0) {
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
            vm.alerts = [];
            vm.backendAlerts = [];
            vm.frontendAlerts = [];
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

    vm.addAlert = function (id, message, level, time, seen) {
        var timer = null;
        var alert = {message: message, level: level, time_created: new Date(), seen: false};
        if(id) {
            alert.id = id;
            alert.seen = seen
            vm.backendAlerts.unshift(alert);
        } else {
            vm.frontendAlerts.unshift(alert);
        }
        if (time) {
            timer = vm.setTimer(alert, time);
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
            vm.removeAlert(alert);
            if(vm.showAlerts) {
                vm.setSeen(vm.alerts.slice(0,5));
            }
        }, time)
    }

    // Listen for show/hide events
    $rootScope.$on('add_top_alert', function (event, data) {
        vm.addAlert(data.id, data.message, data.level, data.time, data.seen);
    });
    $rootScope.$on('add_unseen_top_alert', function (event, data) {
        vm.updateUnseen(data.unseen_count);
        vm.addAlert(data.id, data.message, data.level, data.time, false);
    });
    $rootScope.$on('show_top_alert', function (event, data) {
        vm.showAlert();
        $timeout(function() {
            vm.showAlerts = true;
            vm.setSeen(vm.alerts.slice(0, 5));
        }, 300);
    });
    $rootScope.$on('hide_top_alert', function (event, data) {
        vm.hideAlert();
    });
    $rootScope.$on('get_top_alerts', function (event, data) {
        vm.getNotifications();
    });

}).factory('TopAlert', function ($rootScope, $q, appConfig, $http) {
    // Keep all pending requests here until they get responses
    var callbacks = {};
    // Create a unique callback ID to map requests to responses
    var currentCallbackId = 0;
    // Create our websocket object with the address to the websocket
    var ws = new WebSocket("ws://localhost:8002/notifications/");
    ws.onopen = function () {
    }

    ws.onmessage = function (message) {
        listener(message.data);
    }

    function listener(data) {
        var messageObj = JSON.parse(data);
        $rootScope.$broadcast('add_unseen_top_alert', {
            id: messageObj.id,
            message: messageObj.message,
            level: messageObj.level,
            count: messageObj.unseen_count
        });
        // If an object exists with callback_id in our callbacks object, resolve it
        if (callbacks.hasOwnProperty(messageObj.callback_id)) {
            $rootScope.$apply(callbacks[messageObj.callback_id].cb.resolve(messageObj.data));
            delete callbacks[messageObj.callbackID];
        }
    }

    // This creates a new callback ID for a request
    function getCallbackId() {
        currentCallbackId += 1;
        if (currentCallbackId > 10000) {
            currentCallbackId = 0;
        }
        return currentCallbackId;
    }

    var service = {
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
            return $http.get(appConfig.djangoUrl + "notifications/", {params: {page_size: 7}}).then(function(response) {
                return response.data;
            })
        },
        getNextNotification: function() {
            return $http.get(appConfig.djangoUrl + "notifications/", {params: {page_size: 1, page: 7}}).then(function(response) {
                return response.data;
            })
        },
        getUnseenNotifications: function(date) {
            return $http.get(appConfig.djangoUrl + "notifications/", {params: {create_date: date}}).then(function(response) {
                return response.data;
            })
        },
        delete: function(id) {
            return $http.delete(appConfig.djangoUrl + "notifications/" + id + "/").then(function(response) {
                return response;
            })
        },
        deleteAll: function() {
            return $http.delete(appConfig.djangoUrl + "notifications/").then(function(response) {
                return response;
            })
        }
    }
    return service;
});
