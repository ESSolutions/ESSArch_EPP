angular.module('essarch.controllers').controller('IpApprovalCtrl', function($scope, $controller, $rootScope, Resource, $interval, $timeout, appConfig, $cookies, $anchorScroll, $translate, listViewService, $http, $q, $state, Requests, ContextMenuBase) {
	var vm = this;
	var ipSortString = ['Received', 'Preserving'];
	$controller('BaseCtrl', { $scope: $scope, vm: vm, ipSortString: ipSortString });

    //Request form data
    $scope.initRequestData = function () {
        vm.request = {
            type: "",
            purpose: "",
            storageMedium: {
                value: "",
                options: ["Disk", "Tape(type1)", "Tape(type2)"]
            },
            appraisal_date: null
        };
    }
    $scope.initRequestData();

    $scope.menuOptions = function(rowType, row) {
        var methods = [];
        methods.push(
            {
                text: $translate.instant("INFORMATION_PACKAGE_INFORMATION"),
                click: function ($itemScope, $event, modelValue, text, $li) {
                    $scope.ip = row;
                    $rootScope.ip = row;
                    vm.ipInformationModal($scope.ip);
                }
            }
        );
        methods.push(
            ContextMenuBase.changeOrganization(
                function () {
                    $scope.ip = row;
                    $rootScope.ip = row;
                    vm.changeOrganizationModal($scope.ip);
                })
            );
        return methods;
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
			return;
		}
		if($scope.select && $scope.ip.object_identifier_value== row.object_identifier_value){
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
            $scope.eventShow = false;
			$scope.ip = row;
			$rootScope.ip = $scope.ip;
		}
		$scope.statusShow = false;
    };
});
