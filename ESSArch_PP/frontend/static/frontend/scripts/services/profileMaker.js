angular.module('myApp').factory('ProfileMakerTemplate', function ($resource, appConfig) {
    return $resource(appConfig.djangoUrl + 'profilemaker-templates/:templateName/:action/', { templateName: "@templateName" }, {
        add: {
            method: "POST"
        },
        remove: {
            method: "DELETE",
            params: { action: "delete-element" }
        },
        get: {
            method: "GET",
        },
        generate: {
            method: "POST",
            params: { action: "generate" }
        },
        edit: {
            method: "PUT",
            params: { action: "update-element" }
        },
        addChild: {
            method: "POST",
            params: {
                action: "add-child",
            },
        },
        deleteElement: {
            method: "DELETE",
            hasBody: true,
            headers: { "Content-type": 'application/json;charset=utf-8' },
            params: {
                action: "delete-element",
            }
        },
        addAttribute: {
            method: "POST",
            params: {
                action: "add-attribute"
            }
        },
        getAttributes: {
            method: "GET",
            params: { action: "get-attributes" }
        },
        updateContainFiles: {
            method: "PUT",
            params: { action: "update-contains-files" }
        }
    });
}).factory('ProfileMakerExtension', function ($resource, appConfig) {
    return $resource(appConfig.djangoUrl + 'profilemaker-extensions/:id/:action/', { id: "@id" }, {
        add: {
            method: "POST"
        }
    });
});