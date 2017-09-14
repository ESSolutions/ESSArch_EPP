angular.module('myApp').controller('TopAlertCtrl', function($timeout, $scope, $rootScope) {
    var vm = this;
    vm.visible = false;
    vm.alerts = [];
    vm.showAlerts = false;

    vm.hideAlert = function() {
        vm.visible = false;
        vm.showAlerts = false;
        vm.alerts.splice(0, 1);
    }

    vm.removeAlert = function(alert) {
        vm.alerts.splice(vm.alerts.indexOf(alert), 1);
        if(vm.alerts.length == 0) {
            vm.showAlerts = false;
        }
    }

    vm.viewAlerts = function() {
        if(vm.alerts.length > 0) {
            vm.showAlerts = !vm.showAlerts;
        }
    }

    /**
     * Show top alert
     * @param msg - Message to show on the the alert
     * @param type - Type of alert, applies a class to the alert
     * @param time - Adds a duration to the alert
     */

    vm.showAlert = function (msg, type, time) {
        var timer = null;
        var alert = {msg: msg, type: type};
        vm.alerts.unshift(alert);            
        if (time) {
            timer = vm.setTimer(alert, time);
        }
    }

    /**
     * Set timer for alert
     * @param time - Timer duration
     */
    vm.setTimer = function (alert, time) {
        return $timeout(function () {
            vm.removeAlert(alert);
        }, time)
    }

    // Listen for show/hide events
    $rootScope.$on('show_top_alert', function(event, data) {
        vm.showAlert(data.msg, data.type, data.time);
    });
    $rootScope.$on('hide_top_alert', function(event, data) {
        vm.hideAlert();
    });

}).factory('TopAlert', function($rootScope) {
    return {
        /**
         * Show top alert
         * @param msg - Message to show on the the alert
         * @param type - Type of alert, applies a class to the alert
         * @param time - Adds a duration to the alert
         */
        show: function(msg, type, time) {
            $rootScope.$broadcast('show_top_alert', { msg: msg, type: type, time: time });
            
        },
        /**
         * Hide top alert
         */
        hide: function() {
            $rootScope.$broadcast('hide_top_alert', {});
            
        }
    }
}).filter('reverse', function() {
    return function(items) {
      return items.slice().reverse();
    };
});
