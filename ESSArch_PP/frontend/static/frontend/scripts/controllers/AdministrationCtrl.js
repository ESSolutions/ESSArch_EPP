angular.module('myApp').controller('AdministrationCtrl', function(StorageObject, StorageMedium, IP, $scope, $rootScope, $controller, $cookies, $http, appConfig) {
    var vm = this;
    vm.ipViewType = $cookies.get('ip-view-type') || 1;
    $scope.selectedObject = {id: "", class: ""};
    vm.storageObjects = []
    $scope.getStorageObjects = function() {
        StorageObject.query().$promise.then(function(data) {
            vm.storageObjects = data;
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
        vm.storage_medium = StorageMedium.get({ id: row.storage_medium }).$promise.then(function(data) {
            return data;
        });
        vm.ip = IP.get({id: row.ip }).$promise.then(function(data) {
            return data;
        });
    }
});
