angular.module('myApp').factory('Workarea', function ($resource, appConfig) {
    return $resource(appConfig.djangoUrl + 'workarea/:id/:action/', {}, {
        query: {
            method: 'GET',
            isArray: true,
            interceptor: {
                response: function (response) {
                    response.resource.$httpHeaders = response.headers;
                    return response.resource;
                }
            },
        },
        preserve: {
            method: 'POST',
            params: { action: "preserve", id: "@id" }
        },
    });
}).factory('WorkareaFiles', function ($resource, appConfig) {
    return $resource(appConfig.djangoUrl + 'workarea-files/:action/', {}, {
        addToDip: {
            method: "POST",
            params: { action: "add-to-dip" }
        },
        removeFile: {
            method: "DELETE",
            hasBody: true,
            headers: { "Content-type": 'application/json;charset=utf-8' },
        },
        addDirectory: {
            method: "POST",
            params: { action: "add-directory" }
        },
    });
});