angular.module('myApp').factory('IP', function ($resource, appConfig) {
    return $resource(appConfig.djangoUrl + 'information-packages/:id/:action/', {}, {
        query: {
            method: 'GET',
            transformResponse: function (data, headers) {
                return { data: JSON.parse(data), headers: headers };
            }
        },
        events: {
            method: 'GET',
            params: {action: "events", id: "@id"},
            transformResponse: function (data, headers) {
                return { data: JSON.parse(data), headers: headers };
            },
        },
        preserve: {
            method: 'POST',
            params: { action: "preserve", id: "@id" }
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