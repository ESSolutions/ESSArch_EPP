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
    vm.tapeDrive = null;
    vm.tapeSlots = [];
    vm.tapeDrives = [];
    vm.robotQueue = [];
    vm.storageMediums = [];
    $scope.requestForm = false;
    $scope.eventlog = false;

    $scope.menuOptions = function(rowType){
        return [];
    }

    $scope.initRequestData = function (types) {
        vm.requestTypes = types;
        vm.request = {
            type: types[0],
            purpose: "",
            storageMedium: null,
        };
    }

    // Getters
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

    $scope.loadRobots = function() {
        $scope.ipLoading = true;
        Storage.getRobots().then(function(robots) {
            vm.robots = robots;
            $scope.ipLoading = false;
        });
    }
    $scope.loadRobots();

    // Click funcitons
    
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

    vm.inventoryClick = function(robot) {
        $scope.initRequestData(["inventory"]);
        $scope.requestForm = true;
        $scope.eventlog = true;
    }
    
    vm.tapeDriveClick = function(tapeDrive) {
        if(tapeDrive == vm.tapeDrive) {
            vm.tapeDrive = null;
            $scope.eventlog = false;
            $scope.requestForm = false;
        } else {
            vm.tapeDrive = tapeDrive;
            var types = [];
            if(!tapeDrive.locked) {
                if(tapeDrive.storage_medium != null) {
                    types.push("unmount");
                } else {
                    types.push("mount");
                }
            } else {
                if(tapeDrive.storage_medium != null) {
                    types.push("unmount_force");
                }
            }
            if(types.includes("mount")) {
                $http.get(appConfig.djangoUrl + "storage-mediums/", {params: {status: 20}}).then(function(response) {
                    vm.storageMediums = response.data;
                });
            }
            $scope.initRequestData(types)
            $scope.requestForm = true;
            $scope.eventlog = true;
        }
    }

    // Actions
    vm.inventoryRobot = function(robot, request) {
        Storage.inventoryRobot(robot).then(function(result) {
            $scope.requestForm = false;
            $scope.eventlog = false;
        });
    }

    vm.mountTapeDrive = function(tapeDrive, request) {
        Storage.mountTapeDrive(tapeDrive, request.storageMedium).then(function() {
            $scope.requestForm = false;
            $scope.eventlog = false;
        });
    }

    vm.unmountTapeDrive = function(tapeDrive, request, force) {
        Storage.unmountTapeDrive(tapeDrive, force).then(function() {
            $scope.requestForm = false;
            $scope.eventlog = false;
        });
    }
    // Requests
	$scope.submitRequest = function(object, request) {
		switch(request.type) {
			case "inventory":
				vm.inventoryRobot(object, request);
				break;
            case "mount":
                vm.mountTapeDrive(vm.tapeDrive, request);
                break;
            case "unmount":
                vm.unmountTapeDrive(vm.tapeDrive, request, false);
                break;
            case "unmount_force":
                vm.unmountTapeDrive(vm.tapeDrive, request, true);
                break;
        }
    }
	
    $scope.closeRequestForm = function() {
        $scope.requestForm = false;
        $scope.eventlog = false;
        vm.tapeDrive = null;
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