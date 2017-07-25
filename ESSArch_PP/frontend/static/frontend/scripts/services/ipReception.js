angular.module('myApp').factory('IPReception', function ($resource, appConfig) {
    return $resource(appConfig.djangoUrl + 'ip-reception/:id/:action/', {}, {
        query: {
            method: 'GET',
            transformResponse: function (data, headers) {
                return { data: JSON.parse(data), headers: headers };
            }
        },
        // TODO
        receive: {
            method: 'POST',
            params: { action: "receive", id: "@id" }
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