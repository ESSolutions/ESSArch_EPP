angular.module('myApp').factory('User', function ($resource, appConfig) {
    return $resource(appConfig.djangoUrl + 'users/:id/:action/', { id: "@id" }, {
        get: {
            method: "GET",
            params: {id: "@id"}
        },
        query: {
            method: "GET",
            params: { id: "@id" },
            isArray: true,
            interceptor: {
                response: function (response) {
                    response.resource.$httpHeaders = response.headers;
                    return response.resource;
                }
            },
        },
    });
});