angular.module('essarch.services').factory('ArchivePolicy', function($resource, appConfig) {
  return $resource(appConfig.djangoUrl + 'archive_policies/:id/:action/', {id: '@id'}, {});
});
