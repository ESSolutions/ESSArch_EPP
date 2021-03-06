angular.module('essarch.services').factory('RobotQueue', function($resource, appConfig) {
  return $resource(
    appConfig.djangoUrl + 'robot-queue/:id/:action/',
    {id: '@id'},
    {
      query: {
        method: 'GET',
        params: {id: '@id'},
        isArray: true,
        interceptor: {
          response: function(response) {
            response.resource.$httpHeaders = response.headers;
            return response.resource;
          },
        },
      },
    }
  );
});
