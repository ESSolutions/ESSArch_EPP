angular.module('myApp').factory('Workarea', function ($resource, appConfig) {
    return $resource(appConfig.djangoUrl + 'workarea/:id/:action/', {}, {
        query: {
            method: 'GET',
            transformResponse: function (data, headers) {
                return { data: JSON.parse(data), headers: headers };
            }
        },
        preserve: {
            method: 'POST',
            params: { action: "preserve", id: "@id" }
        },
    });
});