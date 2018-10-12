angular.module('essarch.services').factory('EventType', function ($resource, appConfig) {
    return $resource(appConfig.djangoUrl + 'event-types/:id/:action/', {}, {
    });
});
