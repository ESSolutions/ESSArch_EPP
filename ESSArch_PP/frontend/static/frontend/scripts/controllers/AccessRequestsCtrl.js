angular.module('myApp').controller('AccessRequestsCtrl', function($scope, $controller) {
    $controller('BaseCtrl', { $scope: $scope });
	console.log("Acces requests");	
});
