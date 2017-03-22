angular.module("myApp").controller("UserSettingsCtrl", function($scope, $rootScope, $http, appConfig, $controller, $cookies, myService, $q, $window) {
    var vm = this;
    $controller('BaseCtrl', {$scope: $scope });
    vm.activeColumns = {chosen: []};
    vm.availableColumns = { options: [], chosen: []};

    $scope.changeIpViewType = function(type) {
        $http({
            method: 'PATCH',
            url: $rootScope.auth.url,
            data: {ip_list_view_type: type}
        }).then(function(response) {
            $window.sessionStorage.setItem("view-type", response.data.ip_list_view_type);
            $rootScope.auth = response.data;
        });

    }

    function loadColumnPicker() {
        vm.allColumns.forEach(function(column) {
            var tempBool = false;
            vm.activeColumns.options.forEach(function(activeColumn) {
                if(column == activeColumn) {
                    tempBool = true;
                }
            });
            if(!tempBool) {
                vm.availableColumns.options.push(column);
            }
        });
    }

    myService.getActiveColumns().then(function(result) {
        vm.activeColumns.options = result.activeColumns;
        vm.allColumns = result.allColumns;
        loadColumnPicker();
    });
    $scope.moveToActive = function(inputArray) {
        inputArray.forEach(function(column) {
            vm.activeColumns.options.push(column);
            vm.availableColumns.options.splice(vm.availableColumns.options.indexOf(column), 1);
        });
        vm.availableColumns.chosen = [];
    }
    $scope.moveToAvailable = function(inputArray) {
        inputArray.forEach(function(column) {
            vm.availableColumns.options.push(column);
            vm.activeColumns.options.splice(vm.activeColumns.options.indexOf(column), 1);
        });
        vm.activeColumns.chosen = [];
    }
    $scope.moveUp = function(elements) {
        var A = vm.activeColumns.options;
        for(i=0; i<elements.length; i++) {
            var from = A.indexOf(elements[i]);
            if(A.indexOf(elements[i]) > i) {
                vm.activeColumns.options.move(from, from-1);
            }
        }
    }

    $scope.moveDown = function(elements) {
        var A = vm.activeColumns.options;
        for(i=elements.length-1; i>=0; i--) {
            var from = A.indexOf(elements[i]);
            if(A.indexOf(elements[i]) < A.length-(elements.length - i)) {
                vm.activeColumns.options.move(from, from+1);
            }
        }
    }
    Array.prototype.move = function (from, to) {
        this.splice(to, 0, this.splice(from, 1)[0]);
    };
    $scope.saveColumns = function() {
        $rootScope.listViewColumns = vm.activeColumns.options;
        vm.activeColumns.chosen = [];
        var updateArray = vm.activeColumns.options.map(function(a){return a.label});
        $http({
            method: 'PATCH',
            url: $rootScope.auth.url,
            data: {ip_list_columns: updateArray}
        }).then(function(response) {
            $rootScope.auth = response.data;
        });
    }
});
