angular.module('myApp').controller('IngestWorkareaCtrl', function($scope, $controller, $rootScope, Resource, $interval, $timeout, appConfig, $cookies, $anchorScroll, $translate, $http, listViewService, Requests) {
    var vm = this;
    var ipSortString = "";
    vm.workarea = 'ingest';

    $controller('BaseCtrl', { $scope: $scope, vm: vm, ipSortString: ipSortString });
    //context menu data
    $scope.menuOptions = function() {
        return [];
    }

    //Click function for Ip table
    $scope.ipTableClick = function(row) {
        if(row.package_type == 1) {
			$scope.select = false;
			$scope.eventlog = false;
			$scope.edit = false;
			$scope.eventShow = false;
            $scope.requestForm = false;
            if ($scope.ip != null && $scope.ip.object_identifier_value == row.object_identifier_value) {
                $scope.ip = null;
                $rootScope.ip = null;
                $scope.filebrowser = false;
            } else {
                $scope.ip = row;
                $rootScope.ip = $scope.ip;
            }
			$scope.initRequestData();
			return;
		}
        if($scope.select && $scope.ip.id == row.id){
            $scope.select = false;
            $scope.eventlog = false;
            $scope.edit = false;
            $scope.eventShow = false;
            $scope.requestForm = false;
            $scope.ip = false;
			$rootScope.ip = false
            $scope.filebrowser = false;
			$scope.initRequestData();
        } else {
            $scope.ip = row;
            $rootScope.ip = $scope.ip;
            $scope.select = true;
            $scope.eventlog = true;
            $scope.edit = true;
            $scope.requestForm = true;
            if (!$scope.eventsShow || $scope.ip.object_identifier_value != row.object_identifier_value) {
                $scope.eventShow = false;
                $scope.eventsClick(row);
            }
            $scope.ip = row;
			$rootScope.ip = $scope.ip;
        }
        $scope.statusShow = false;
    };
});
