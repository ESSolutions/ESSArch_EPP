angular.module('myApp').controller('AccessWorkareaCtrl', function($scope, $controller, $rootScope, Resource, $interval, $timeout, appConfig, $cookies, $anchorScroll, $translate, $state, $http, listViewService, Requests) {
    var vm = this;
    var ipSortString = "";
    vm.archived = true;
    vm.workarea = 'access';

    $controller('BaseCtrl', { $scope: $scope, vm: vm, ipSortString: ipSortString });

    $scope.menuOptions = function() {
        return [
            [$translate.instant('APPLYCHANGES'), function ($itemScope, $event, modelValue, text, $li) {
            }],
        ];
    }

    //Click function for Ip table
    $scope.ipTableClick = function(row) {
        if(row.package_type == 1) {
			$scope.select = false;
			$scope.eventlog = false;
			$scope.edit = false;
			$scope.eventShow = false;
			$scope.requestForm = false;
			$scope.initRequestData();
			if ($scope.ip != null && $scope.ip.object_identifier_value== row.object_identifier_value) {
				$scope.ip = null;
				$rootScope.ip = null;
                $scope.filebrowser = false;
			} else {
				$scope.ip = row;
				$rootScope.ip = $scope.ip;
			}
			return;
		}
        if($scope.select && $scope.ip.object_identifier_value == row.object_identifier_value){
            $scope.select = false;
            $scope.eventlog = false;
            $scope.edit = false;
            $scope.eventShow = false;
            $scope.requestForm = false;
            $scope.ip = null;
            $rootScope.ip = null;
            $scope.filebrowser = false;
            $scope.initRequestData();
        } else {
            $scope.select = true;
            $scope.eventlog = true;
            $scope.edit = true;
            $scope.requestForm = true;
            if (!$scope.eventsShow || $scope.ip.object_identifier_value != row.object_identifier_value) {
                $scope.eventShow = false;
                $scope.eventsClick(row);
            };
            $scope.ip = row;
            $rootScope.ip = $scope.ip;
        }
        $scope.statusShow = false;
    };
});
