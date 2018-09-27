angular.module('essarch.services').factory('IOQueue', function ($resource, appConfig) {
    return $resource(appConfig.djangoUrl + 'io-queue/:id/:action/', { id: "@id" }, {
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
