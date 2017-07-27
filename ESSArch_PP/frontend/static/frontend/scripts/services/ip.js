angular.module('myApp').factory('IP', function ($resource, appConfig, Event) {
    return $resource(appConfig.djangoUrl + 'information-packages/:id/:action/', {}, {
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
        events: {
            method: 'GET',
            params: {action: "events", id: "@id"},
            isArray: true,
            interceptor: {
                response: function (response) {
                    response.resource.forEach(function(res, idx, array) {
                        array[idx] = new Event(res);
                    });
                    response.resource.$httpHeaders = response.headers;
                    return response.resource;
                }
            },
        },
        prepareDip: {
            method: "POST",
            params: { action: "prepare-dip" }
        },
        createDip: {
            method: "POST",
            params: { action: "create-dip", id: "@id" }
        },
        files: {
            method: "GET",
            params: { action: "files", id: "@id" },
            isArray: true
        },
        addFile: {
            method: "POST",
            params: { action: "files" , id: "@id" }
        },
        removeFile: {
            method: "DELETE",
            hasBody: true,
            params: { action: "files", id: "@id" },
            headers: { "Content-type": 'application/json;charset=utf-8' },
        },
        preserve: {
            method: 'POST',
            isArray: true,
            params: { action: "preserve", id: "@id" }
        },
        access: {
            method: "POST",
            params: { action: "access", id: "@id" }
        },
        changeSa: {
            method: "PATCH",
            params: { id: "@id" },
        },
        submit: {
            method: 'POST',
            params: { action: "submit", id: "@id" }
        },
    });
});