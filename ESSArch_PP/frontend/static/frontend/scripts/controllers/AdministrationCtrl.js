angular.module('myApp').controller('AdministrationCtrl', function($scope, $rootScope, $controller, $cookies, $http, appConfig) {
    var vm = this;
    $controller('BaseCtrl', { $scope: $scope });
    vm.ipViewType = $cookies.get('ip-view-type') || 1;
    $scope.selectedObject = {id: "", class: ""};

    vm.storageObjects = []
    $scope.getStorageObjects = function() {
        $http.get(appConfig.djangoUrl + 'storage-objects').then(function(response) {
            vm.storageObjects = response.data;
        });
    }
    $scope.getStorageObjects();

    $scope.selectObject = function(row) {
        vm.storageObjects.forEach(function(object) {
            if(object.id == $scope.selectedObject.id){
                object.class = "";
            }
        });
    }

    $scope.objectTableClick = function(row) {
        vm.storage_medium = $http.get(row.storage_medium).then(function(response) {
            return response.data;
        });
        vm.ip = $http.get(row.ip).then(function(response) {
            return response.data;
        });
    }
});
