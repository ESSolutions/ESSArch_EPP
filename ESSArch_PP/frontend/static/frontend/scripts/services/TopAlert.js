angular.module('myApp').factory('TopAlert', function ($rootScope, $q, appConfig, $http, $window) {
    // Keep all pending requests here until they get responses
    var callbacks = {};
    // Create a unique callback ID to map requests to responses
    var currentCallbackId = 0;
    // Create our websocket object with the address to the websocket
    var ws = new WebSocket(appConfig.webSocketProtocol + "://" + $window.location.host + "/ws/");
    ws.onopen = function () {
        $rootScope.useWebsocket = true;
    }

    ws.onclose = function () {
        $rootScope.useWebsocket = false;
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
