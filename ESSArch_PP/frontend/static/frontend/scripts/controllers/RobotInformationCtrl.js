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

angular.module('myApp').controller('RobotInformationCtrl', function($scope, $controller, $rootScope, $http, Resource, appConfig, $timeout, $anchorScroll, $translate, Storage){
    var vm = this;
    $scope.translate = $translate;
    vm.slotsPerPage = 20;
    $scope.colspan = 4;
    vm.robots = [];
    $scope.select = false;
    vm.selectedRobot = null;
    vm.tapeSlots = [];
    vm.tapeDrives = [];
    vm.robotQueue = [];
    $scope.requestForm = false;
    $scope.eventlog = false;

    $scope.menuOptions = function(rowType){
        return [];
    }

    $scope.initRequestData = function () {
        vm.request = {
            type: "inventory",
            purpose: "",
        };
    }
    $scope.initRequestData();

    $scope.getDrives = function(robot) {
        Storage.getTapeDrives(robot).then(function(drives) {
            vm.tapeDrives = drives;
        });
    }

    $scope.getSlots = function(robot) {
        Storage.getTapeSlots(robot).then(function(slots) {
            vm.tapeSlots = slots;
        });
    }

    $scope.getRobotQueue = function(robot) {
        Storage.getRobotQueue(robot).then(function(queue) {
            vm.robotQueue = queue;
        });
    }

    $scope.robotClick = function(robot) {
        if($scope.select && vm.selectedRobot.id == robot.id){
            $scope.select = false;
            $scope.edit = false;
            $scope.eventlog = false;
            $scope.requestForm = false;
            vm.selectedRobot = null;
        } else {
            vm.selectedRobot = robot;
            $scope.select = true;
            $scope.getSlots(vm.selectedRobot);
            $scope.getDrives(vm.selectedRobot);
            $scope.getRobotQueue(vm.selectedRobot);
        }
    }

    $scope.loadRobots = function() {
        $scope.ipLoading = true;
        Storage.getRobots().then(function(robots) {
            vm.robots = robots;
            $scope.ipLoading = false;
        });
    }
    $scope.loadRobots();

    vm.inventoryClick = function(robot) {
        $scope.initRequestData();
        $scope.requestForm = true;
        $scope.eventlog = true;
    }
    vm.inventoryRobot = function(robot, request) {
        Storage.inventoryRobot(robot).then(function(result) {
            $scope.requestForm = false;
            $scope.eventlog = false;
        });
    }

    // Requests
	$scope.submitRequest = function(robot, request) {
		switch(request.type) {
			case "inventory":
				vm.inventoryRobot(robot, request);
				break;
        }
    }
	
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