angular.module('myApp').controller('AppraisalCtrl', function(ArchivePolicy, $scope, $controller, $rootScope, $cookies, $stateParams, appConfig, $http) {
    var vm = this;
    $scope.tag = $stateParams.tag;
    $scope.ips = $stateParams.ips;
    $scope.archivePolicy = $stateParams.archive_policy;

    function getArchivePolicies() {
        ArchivePolicy.query().$promise.then(function(data) {
            vm.archivePolicies = data;
        });
    }
    getArchivePolicies();
});
