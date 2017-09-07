angular.module('myApp').factory('Sysinfo', function ($resource, appConfig) {
    return $resource(appConfig.djangoUrl + 'sysinfo/', { id: "@id" }, {
        get: {
            method: "GET"
        }
    });
});
