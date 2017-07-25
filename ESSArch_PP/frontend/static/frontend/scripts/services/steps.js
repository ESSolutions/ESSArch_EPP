angular.module('myApp').factory('Steps', function ($resource, appConfig) {
    return $resource(appConfig.djangoUrl + 'steps/:id/:action/', {}, {
        query: {
            method: 'GET',
            isArray: true,
        },
        preserve: {
            method: 'POST',
            params: { action: "preserve", id: "@id" }
        },
    });
});