angular.module('myApp').factory('IP', function ($resource, appConfig, Event, Step) {
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
        delete: {
            method: 'DELETE',
            params: { id: "@id" }
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
        steps: {
            method: "GET",
            params: { action: "steps", id: "@id" },
            isArray: true,
            interceptor: {
                response: function (response) {
                    response.resource.forEach(function(res, idx, array) {
                        array[idx] = new Step(res);
                    });
                    response.resource.$httpHeaders = response.headers;
                    return response.resource;
                }
            },
        },
        checkProfile: {
            method: "PUT",
            params: { method: "check-profile", id: "@id" }
        },
        unlockProfile: {
            method: "POST",
            params: { action: "unlock-profile", id: "@id" }
        },
        changeProfile: {
            method: "PUT",
            params: { action: "change-profile", id: "@id" }
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
            params: { action: "access", id: "@id" },
            isArray: true
        },
        changeSa: {
            method: "PATCH",
            params: { id: "@id" },
        },
        submit: {
            method: 'POST',
            params: { action: "submit", id: "@id" }
        },
        moveToApproval: {
            method: 'POST',
            params: { action: "receive", id: "@id" }
        }
    });
});
