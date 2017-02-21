angular.module('myApp').controller('AccessAipCtrl', function($scope, $controller) {
    $controller('BaseCtrl', { $scope: $scope });
	console.log("Access aip");	
});
