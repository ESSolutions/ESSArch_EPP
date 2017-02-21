angular.module('myApp').controller('IngestWorkareaCtrl', function($scope, $controller) {
    $controller('BaseCtrl', { $scope: $scope });
    $scope.message = "Ingest workarea";
    console.log($scope.message);
});
