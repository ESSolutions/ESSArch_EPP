angular.module('myApp').controller('IpApprovalCtrl', function($scope, $controller) {
    $controller('BaseCtrl', { $scope: $scope });
    $scope.message = "ip approval";
    console.log($scope.message);
});
