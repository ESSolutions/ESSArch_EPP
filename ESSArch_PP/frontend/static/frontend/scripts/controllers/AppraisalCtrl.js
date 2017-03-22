angular.module('myApp').controller('AppraisalCtrl', function($scope, $controller, $rootScope, $cookies, $stateParams, appConfig, $http) {
    var vm = this;
    $controller('BaseCtrl', { $scope: $scope });
    $scope.tag = $stateParams.tag;
    $scope.ips = $stateParams.ips;
    $scope.archivePolicy = $stateParams.archive_policy;

    function getArchivePolicies() {
        $http.get(appConfig.djangoUrl + "archive_policies/").then(function(response) {
            vm.archivePolicies = response.data;
        });
    }
    getArchivePolicies();
});
