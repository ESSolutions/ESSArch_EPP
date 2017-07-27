angular.module('myApp').factory('Task', function ($resource, appConfig) {
    return $resource(appConfig.djangoUrl + 'tasks/:id/:action/', { id: "@id" }, {
        get: {
            method: "GET",
            params: { id: "@id" }
        },
        undo: {
            method: "POST",
            params: { action: "undo", id: "@id" }
        },
        retry: {
            method: "POST",
            params: { action: "retry", id: "@id" }
        }
    });
});