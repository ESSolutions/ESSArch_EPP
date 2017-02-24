angular.module('myApp').controller('CreateDipCtrl', function($scope, $state, $stateParams, $controller) {
    $controller('BaseCtrl', { $scope: $scope });
    var vm = this;
    console.log($stateParams);
});
