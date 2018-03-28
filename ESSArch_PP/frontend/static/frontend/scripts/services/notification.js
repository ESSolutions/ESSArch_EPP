angular.module('myApp').factory('Notification', function($http, appConfig) {
    var service = {};

    service.getNotifications = function(pageNumber, pageSize, sortString, searchString) {
        return $http({
            method: 'GET',
            url: appConfig.djangoUrl + "notifications/",
            params: {
                page: pageNumber,
                page_size: pageSize,
                ordering: sortString,
                search: searchString,
            }
        }).then(function(response) {
            var count = response.headers('Count');
            if (count == null) {
                count = response.data.length;
            }
            return {
                count: count,
                data: response.data
            };
        })
    }
    service.remove = function(id) {
        return $http.delete(appConfig.djangoUrl + "notifications/" + id + "/").then(function(response) {
            return response;
        })
    }

    return service;
})
