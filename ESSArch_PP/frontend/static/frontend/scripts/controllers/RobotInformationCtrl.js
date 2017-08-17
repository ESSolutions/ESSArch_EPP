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

angular.module('myApp').controller('RobotInformationCtrl', function(StorageMedium, $scope, $controller, $interval, $rootScope, $http, Resource, appConfig, $timeout, $anchorScroll, $translate, Storage){
    var vm = this;
    $scope.translate = $translate;
    vm.slotsPerPage = 10;
    $scope.colspan = 4;
    vm.robots = [];
    $scope.select = false;
    vm.selectedRobot = null;
    vm.tapeDrive = null;
    vm.tapeSlot = null;
    vm.tapeSlots = [];
    vm.tapeDrives = [];
    vm.robotQueue = [];
    vm.storageMediums = [];
    $scope.requestForm = false;
    $scope.eventlog = false;

    // Table states

    var robotInterval;
    $rootScope.$on('$stateChangeStart', function() {
		$interval.cancel(robotInterval);
	});
    $interval.cancel(robotInterval);
    robotInterval = $interval(function() {
        vm.updateTables();
    }, appConfig.robotInterval);

    vm.updateTables = function() {
        $scope.loadRobots(vm.robotTableState);
        if(vm.selectedRobot != null) {
            $scope.getRobotQueue(vm.robotQueueTableState)
            $scope.getSlots(vm.slotTableState);
            $scope.getDrives(vm.driveTableState);
        }
    }
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
    $scope.getDrives = function(tableState) {
        if (!angular.isUndefined(tableState)) {
            vm.driveTableState = tableState;
            var search = "";
			if(tableState.search.predicateObject) {
				var search = tableState.search.predicateObject["$"];
			}
			var sorting = tableState.sort;
			var pagination = tableState.pagination;
			var start = pagination.start || 0;     // This is NOT the page number, but the index of item in the list that you want to use to display the table.
			var number = pagination.number || vm.drivesPerPage;  // Number of entries showed per page.
			var pageNumber = start/number+1;
            Resource.getTapeDrives(start, number, pageNumber, tableState, sorting, search, vm.selectedRobot).then(function (result) {
                vm.tapeDrives = result.data;
                tableState.pagination.numberOfPages = result.numberOfPages;//set the number of pages so the pagination can update
            });
        }
    }

    $scope.getSlots = function (tableState) {
        if (!angular.isUndefined(tableState)) {
            vm.slotTableState = tableState;
            var search = "";
			if(tableState.search.predicateObject) {
				var search = tableState.search.predicateObject["$"];
			}
			var sorting = tableState.sort;
			var pagination = tableState.pagination;
			var start = pagination.start || 0;     // This is NOT the page number, but the index of item in the list that you want to use to display the table.
			var number = pagination.number || vm.slotsPerPage;  // Number of entries showed per page.
			var pageNumber = start/number+1;
            Resource.getTapeSlots(start, number, pageNumber, tableState, sorting, search, vm.selectedRobot).then(function (result) {
                vm.tapeSlots = result.data;
                tableState.pagination.numberOfPages = result.numberOfPages;//set the number of pages so the pagination can update
            });
        }
    }

    $scope.getRobotQueue = function (tableState) {
        if (!angular.isUndefined(tableState)) {
            vm.robotQueueTableState = tableState;
            var search = "";
			if(tableState.search.predicateObject) {
				var search = tableState.search.predicateObject["$"];
			}
			var sorting = tableState.sort;
			var pagination = tableState.pagination;
			var start = pagination.start || 0;     // This is NOT the page number, but the index of item in the list that you want to use to display the table.
			var number = pagination.number || vm.robotQueueItemsPerPage;  // Number of entries showed per page.
			var pageNumber = start/number+1;
            Resource.getRobotQueueForRobot(start, number, pageNumber, tableState, sorting, search, vm.selectedRobot).then(function (result) {
                vm.robotQueue = result.data;
                tableState.pagination.numberOfPages = result.numberOfPages;//set the number of pages so the pagination can update
            });
        }
    }

    $scope.loadRobots = function(tableState) {
        $scope.ipLoading = true;
        if (!angular.isUndefined(tableState)) {
            vm.robotTableState = tableState;
            var search = "";
			if(tableState.search.predicateObject) {
				var search = tableState.search.predicateObject["$"];
			}
			var sorting = tableState.sort;
			var pagination = tableState.pagination;
			var start = pagination.start || 0;     // This is NOT the page number, but the index of item in the list that you want to use to display the table.
			var number = pagination.number || vm.robotsPerPage;  // Number of entries showed per page.
			var pageNumber = start/number+1;
            Resource.getRobots(start, number, pageNumber, tableState, sorting, search).then(function (result) {
                vm.robots = result.data;
                tableState.pagination.numberOfPages = result.numberOfPages;//set the number of pages so the pagination can update
                $scope.ipLoading = false;
            });
        }
    }

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
            $scope.getSlots(vm.slotTableState);
            $scope.getDrives(vm.driveTableState);
            $scope.getRobotQueue(vm.robotQueueTableState);
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
            vm.tapeSlot = null;
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
                vm.getStorageMediumsByState(20).then(function(result) {
                    vm.storageMediums = result;
                });
            }
            $scope.initRequestData(types)
            $scope.requestForm = true;
            $scope.eventlog = true;
        }
    }

    vm.tapeSlotClick = function (tapeSlot) {
        if (tapeSlot.medium_id === "") {
            return;
        }
        if (tapeSlot == vm.tapeSlot) {
            vm.tapeSlot = null;
            $scope.eventlog = false;
            $scope.requestForm = false;
        } else {
            vm.tapeDrive = null;
            vm.tapeSlot = tapeSlot;
            var types = [];
            if (!tapeSlot.locked) {
                if (tapeSlot.mounted) {
                    types.push("unmount");
                } else {
                    types.push("mount");
                }
            } else {
                if (tapeSlot.mounted) {
                    types.push("unmount_force");
                }
            }
            $scope.initRequestData(types)
            $scope.requestForm = true;
            $scope.eventlog = true;
        }
    }

    vm.getStorageMediumsByState = function (status) {
        return StorageMedium.query({status : status }).$promise.then(function (data) {
            return data;
        });
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

    vm.mountTapeSlot = function(tapeSlot, request) {
        Storage.mountTapeSlot(tapeSlot, request).then(function() {
            $scope.requestForm = false;
            $scope.eventlog = false;
        });
    }

    vm.unmountTapeSlot = function(tapeSlot, request, force) {
        Storage.unmountTapeSlot(tapeSlot, force).then(function() {
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
                if(vm.tapeDrive != null) {
                    vm.mountTapeDrive(vm.tapeDrive, request);
                } else if (vm.tapeSlot != null) {
                    vm.mountTapeSlot(vm.tapeSlot, request);
                }
                break;
            case "unmount":
                if(vm.tapeDrive != null) {
                    vm.unmountTapeDrive(vm.tapeDrive, request, false);
                } else if (vm.tapeSlot != null) {
                    vm.unmountTapeSlot(vm.tapeSlot, request, false);
                }
                break;
            case "unmount_force":
                if(vm.tapeDrive != null) {
                    vm.unmountTapeDrive(vm.tapeDrive, request, true);
                } else if (vm.tapeSlot != null) {
                    vm.unmountTapeSlot(vm.tapeSlot, request, true);
                }
                break;
        }
    }

    $scope.closeRequestForm = function() {
        $scope.requestForm = false;
        $scope.eventlog = false;
        vm.tapeDrive = null;
        vm.tapeSlot = null;
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