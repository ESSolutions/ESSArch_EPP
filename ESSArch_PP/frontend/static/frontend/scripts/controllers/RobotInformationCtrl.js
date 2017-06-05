/*
ESSArch is an open source archiving and digital preservation system

ESSArch Preservation Platform (EPP)
Copyright (C) 2005-2017 ES Solutions AB

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.

Contact information:
Web - http://www.essolutions.se
Email - essarch@essolutions.se
*/

angular.module('myApp').controller('RobotInformationCtrl', function($scope, $controller, $rootScope, $http, Resource, appConfig, $timeout, $anchorScroll, $translate){
    var vm = this;
    $scope.translate = $translate;
    $controller('BaseCtrl', { $scope: $scope});
    vm.slotsPerPage = 20;
    $scope.colspan = 4;
    vm.robots = [];
    $scope.select = false;
    vm.selectedRobot = null;
    vm.tapeSlots = [];
    vm.tapeDrives = [];

    $scope.robotRowClick = function(row) {
		$scope.selectRobotObj(row);
		if($vm.selectedRobot.ip == row){
            vm.selectedRobot = null;
		}
		if($scope.eventShow) {
			$scope.eventsClick(row);
		}
		if($scope.statusShow) {
			$scope.stateClicked(row);
		}
		if ($scope.select) {
			$scope.robotClick(row);
		}
	}

    $scope.getDrives = function(robot) {
        $http.get(robot.url + "tape-drives/").then(function(response) {
            vm.tapeDrives = response.data;
        });
    }

    $scope.getSlots = function(robot) {
        $http.get(robot.url + "tape-slots/").then(function(response) {
            vm.tapeSlots = response.data;
        });
    }

    $scope.robotClick = function(robot) {
        if($scope.select && vm.selectedRobot.id == robot.id){
            $scope.select = false;
            $scope.edit = false;
            $scope.eventlog = false;
            vm.selectedRobot = null;
        } else {
            vm.selectedRobot = robot;
            $scope.select = true;
            $scope.getSlots(vm.selectedRobot);
            $scope.getDrives(vm.selectedRobot);
        }
    }

    $scope.loadRobots = function() {
        $scope.ipLoading = true;
        $http.get(appConfig.djangoUrl + 'robots/').then(function(response) {
            vm.robots = response.data;
            $scope.ipLoading = false;
        });
    }
    $scope.loadRobots();
    $scope.searchDisabled = function () {
        if ($scope.filterModels.length > 0) {
            if ($scope.filterModels[0].column != null) {
                delete $scope.tableState.search.predicateObject;
                return true;
            }
        } else {
            return false;
        }
    }
    $scope.clearSearch = function () {
        delete $scope.tableState.search.predicateObject;
        $('#search-input')[0].value = "";
        $scope.getListViewData();
    }
});