angular.module('myApp').factory('Profile', function ($resource, appConfig) {
    return $resource(appConfig.djangoUrl + 'profiles/:id/:action/?pager=none', {}, {
    get: {
        method: "GET",
        params: { id: "@id" }
    }
    });
})
.factory('ProfileIp', function ($resource, appConfig) {
    return $resource(appConfig.djangoUrl + 'profile-ip/:id/', {}, {
    query: {
        method: "GET",
        isArray: true,
    },
    get: {
        method: "GET",
    },
    post: {
        method: "POST",
    },
    patch: {
        method: "PATCH",
        params: { id: "@id" }
    }
    });
})
.factory('ProfileIpData', function ($resource, appConfig) {
    return $resource(appConfig.djangoUrl + 'profile-ip-data/:id/:action/', {}, {
    get: {
        method: "GET",
        params: { id: "@id" }
    },
    post: {
        method: "POST",
    },
    });
});
