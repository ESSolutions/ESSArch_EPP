angular.module('myApp').factory('Orders', function ($resource, appConfig) {
    return $resource(appConfig.djangoUrl + 'orders/:id/:action/', {}, {
        query: {
            method: 'GET',
            transformResponse: function (data, headers) {
                return { data: JSON.parse(data), headers: headers };
            }
        },
    });
});