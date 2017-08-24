angular.module('myApp').factory('Profile', function ($resource, appConfig) {
    return $resource(appConfig.djangoUrl + 'profiles/:id/:action/', {id: "@id"}, {
    get: {
        method: "GET",
    }
    });
})
.factory('ProfileIpData', function ($resource, appConfig) {
    return $resource(appConfig.djangoUrl + 'profile-ip-data/:action/', {}, {
    get: {
        method: "GET",
    },
    post: {
        method: "POST",
    },
    });
});