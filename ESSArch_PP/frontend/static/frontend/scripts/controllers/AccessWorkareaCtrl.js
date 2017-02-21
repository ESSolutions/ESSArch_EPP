angular.module('myApp').controller('AccessWorkareaCtrl', function($scope, $controller) {
    $controller('BaseCtrl', { $scope: $scope });
	console.log("Acces workarea");	
});
