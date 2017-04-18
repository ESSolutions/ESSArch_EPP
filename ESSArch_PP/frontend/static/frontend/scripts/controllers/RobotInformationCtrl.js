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
    $scope.selectedRobotObj = {id: "", class: ""};
    
    
    $scope.selectRobotObj = function(row) {
        vm.robots.forEach(function(robot) {
            if(robot.id == $scope.selectedRobotObj.id){
                robot.class = "";
            }
        });
        if(row.id == $scope.selectedRobotObj.id){
            $scope.selectedRobotObj = {id: "", class: ""};
        } else {
            row.class = "selected";
            $scope.selectedRobotObj = row;
        }
    };
    
    $scope.robotRowClick = function(row) {
		$scope.selectRobotObj(row);
		if($scope.ip == row){
			row.class = "";
			$scope.selectedRobotObj = {id: "", class: ""};
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
        } else {
            vm.selectedRobot = robot;
            $scope.select = true;
            $scope.getSlots(vm.selectedRobot);
            $scope.getDrives(vm.selectedRobot);
            $timeout(function() {
                $anchorScroll("select-view");
            }, 0);
        }
    }
    
    $scope.loadRobots = function() {
        $http.get(appConfig.djangoUrl + 'robots/').then(function(response) {
            vm.robots = response.data;
        });
    }
    $scope.loadRobots();
});