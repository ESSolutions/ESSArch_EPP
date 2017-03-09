angular.module('myApp').controller('AdministrationCtrl', function($scope, $rootScope, $controller, $cookies) {
    var vm = this;
    $controller('BaseCtrl', { $scope: $scope });
    vm.ipViewType = $cookies.get('ip-view-type') || 1;
});
