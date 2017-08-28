angular.module('myApp').controller('IpApprovalCtrl', function($scope, $controller, $rootScope, Resource, $interval, $timeout, appConfig, $cookies, $anchorScroll, $translate, listViewService, $http, $q, $state, Requests) {
	var vm = this;
	var ipSortString = "Received,Preserving";
	$controller('BaseCtrl', { $scope: $scope, vm: vm, ipSortString: ipSortString });

	$scope.menuOptions = function(rowType) {
		return [
		[$translate.instant("APPRAISAL"), function ($itemScope, $event, modelValue, text, $li) {
			var row;
			if(rowType === "row") {
				row = $itemScope.row;
			} else {
				row = $itemScope.subrow;
				row.information_packages = [];
			}
			var ips = [];
			if(row.information_packages.length>0) {
				if(row.package_type != 1) {
					ips.push(row.url);
				}
				row.information_packages.forEach(function(ip) {
					if(ip.url) {
						ips.push(ip.url);
					} else {
						ips.push(ip);
					}
				});
			} else {
				ips.push(row.url);
			}
			$state.go("home.appraisal", {tag: null, ips: ips, archive_policy: null});
		}]
		];
	};

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
			if(!$scope.eventsShow || $scope.ip.object_identifier_value != row.object_identifier_value) {
				$scope.eventShow = false;
				$scope.eventsClick(row);
			}
			$scope.ip = row;
			$rootScope.ip = $scope.ip;
		}
		$scope.statusShow = false;
    };
});
