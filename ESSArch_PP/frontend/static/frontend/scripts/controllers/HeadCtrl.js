angular
  .module('essarch.controllers')
  .controller('HeadCtrl', function($scope, $rootScope, $timeout, $translate, $state) {
    var vm = this;
    var appName = ' | ESSArch Preservation Platform';
    vm.pageTitle = 'ESSArch Preservation Platform';
    $scope.$on('$stateChangeSuccess', function(event, toState, toParams, fromState, fromParams) {
      vm.pageTitle =
        $translate.instant(
          toState.name
            .split('.')
            .pop()
            .toUpperCase()
        ) + appName;
    });
    $scope.$on('$translateChangeSuccess', function() {
      vm.pageTitle =
        $translate.instant(
          $state.current.name
            .split('.')
            .pop()
            .toUpperCase()
        ) + appName;
    });
    $rootScope.$on('UPDATE_TITLE', function(event, data) {
      vm.pageTitle = data.title + appName;
    });
  });
