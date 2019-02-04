angular.module('essarch.services').factory('TapeSlot', function($resource, appConfig) {
  return $resource(
    appConfig.djangoUrl + 'tape-slots/:id/:action/',
    {id: '@id'},
    {
      get: {
        method: 'GET',
        params: {id: '@id'},
      },
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
