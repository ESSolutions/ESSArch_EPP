angular.module('myApp').factory('EventType', function ($resource, appConfig) {
    return $resource(appConfig.djangoUrl + 'event-types/:id/:action/', {}, {
    });
});
