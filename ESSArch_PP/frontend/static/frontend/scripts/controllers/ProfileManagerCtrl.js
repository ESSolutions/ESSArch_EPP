angular
  .module('essarch.controllers')
  .controller('ProfileManagerCtrl', function($state, $scope, $rootScope, Requests, listViewService) {
    $scope.welcome = 'Welcome to the Profile Manager';
    $scope.select = true;
    $scope.$state = $state;
  });
