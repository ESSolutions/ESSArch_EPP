angular.module('myApp').factory('EventTypes', function ($resource, appConfig) {
    return $resource(appConfig.djangoUrl + 'event-types/:id/:action/', {}, {
    });
});