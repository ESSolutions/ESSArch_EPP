angular.module('myApp').factory('Tag', function ($resource, appConfig) {
    var Tag = $resource(appConfig.djangoUrl + 'tags/:id/:action/', { id: "@id" }, {
        get: {
            method: "GET",
            params: { id: "@id" },
            interceptor: {
                response: function (response) {
                    response.resource.children.forEach(function (child, idx, array) {
                        array[idx] = new Tag(child);
                    });
                    response.resource.$httpHeaders = response.headers;
                    return response.resource;
                }
            },
        },
        query: {
            method: "GET",
            params: { id: "@id" },
            isArray: true,
            interceptor: {
                response: function (response) {
                    response.resource.forEach(function (res) {
                        res.children.forEach(function (child, idx, array) {
                            array[idx] = new Tag(child);
                        });
                    });
                    response.resource.$httpHeaders = response.headers;
                    return response.resource;
                }
            },
        },
        update: {
            method: "PATCH",
            params: { id: "@id" }
        }
    });
    return Tag;
});