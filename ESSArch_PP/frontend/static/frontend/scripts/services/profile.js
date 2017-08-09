angular.module('myApp').factory('Profile', function ($resource, appConfig) {
    return $resource(appConfig.djangoUrl + 'profiles/:id/:action/', {id: "@id"}, {
    get: {
        method: "GET",
    }
    });
});