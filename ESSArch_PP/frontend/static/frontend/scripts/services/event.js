angular.module('myApp').factory('Event', function ($resource, appConfig) {
    return $resource(appConfig.djangoUrl + 'events/:id/:action/', {}, {
        query: {
            method: 'GET',
            transformResponse: function (data, headers) {
                return { data: JSON.parse(data), headers: headers };
            }
        }
    });
});