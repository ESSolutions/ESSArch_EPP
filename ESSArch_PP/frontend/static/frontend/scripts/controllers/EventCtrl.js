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

angular.module('myApp').controller('EventCtrl', ['Resource', '$scope', '$rootScope', 'listViewService', '$interval', 'appConfig', '$cookies', function (service, $scope, $rootScope, listViewService, $interval, appConfig, $cookies) {
    var vm = this;
    vm.itemsPerPage = $cookies.get('epp-events-per-page') || 10;
    $scope.updateEventsPerPage = function(items) {
        $cookies.put('epp-events-per-page', items);
    };
    $scope.selected = [];
    vm.displayed = [];
    $scope.addEventAlert = null;
    $scope.alerts = {
        addEventError: { type: 'danger', msg: 'ERROR_MESSAGE' },
        addEventSuccess: { type: 'success', msg: 'EVENT_ADDED' }
    };
    $scope.closeAlert = function() {
        $scope.addEventAlert = null;
    }
    $rootScope.$on('$stateChangeStart', function() {
        $interval.cancel(eventInterval);
    });
    $scope.$on("$destroy", function() {
        $interval.cancel(eventInterval);
    });
    $rootScope.$watch(function() {return $rootScope.ip;}, function(){
        $scope.addEventAlert = null;
    });
    $scope.newEventForm = {
        eventType: "",
        eventOutcome: "",
        comment: ""
    };
    $scope.eventLevels = {
        10: 'debug',
        20: 'info',
        30: 'warning',
        40: 'error',
        50: 'critical',
    };
    $scope.getEventOutcome = function(outcome) {
        level = $scope.eventLevels[outcome];
        return level.charAt(0).toUpperCase() + level.slice(1)
    }
    $scope.eventOutcomes = function(){
        levels = $scope.eventLevels;
        return Object.keys(levels).map(function(k) {
            return {value: k, name: levels[k]};
        });
    }()
    //Event click funciton
    $scope.eventClick = function(row) {
        if(row.class == "selected"){
            row.class = "";
            for(i=0; i<$scope.selected.length; i++){
                if($scope.selected[i].id === row.id){
                    $scope.selected.splice(i,1);
                }
            }
        } else {
            row.class = "selected";
            $scope.selected.push(row);
        }
    };
    $scope.addEvent = function(ip, eventType, eventDetail, eventOutcome) {
        $scope.addEventAlert = null;
        listViewService.addEvent(ip, eventType, eventDetail, eventOutcome).then(function(value) {
            $rootScope.stCtrl.pipe();
            $scope.addEventAlert = $scope.alerts.addEventSuccess;
            $scope.newEventForm = {
                eventType: "",
                eventOutcome: "",
                comment: ""
            };
        }).catch(function error() {
            $scope.addEventAlert = $scope.alerts.addEventError;
        });
    }
    var eventInterval;
    function updateEvents() {
        $interval.cancel(eventInterval);
        eventInterval = $interval(function() {
            $rootScope.stCtrl.pipe();
        }, appConfig.eventInterval);
    }
    updateEvents();
    //Get data from rest api for event table
    $scope.eventPipe = function(tableState, ctrl) {
        $scope.eventLoading = true;
        if(vm.displayed.length == 0) {
            $scope.initLoad = true;
        }
        $rootScope.stCtrl = ctrl;
        var sorting = tableState.sort;
        var pagination = tableState.pagination;
        var start = pagination.start || 0;     // This is NOT the page number, but the index of item in the list that you want to use to display the table.
        var number = pagination.number || vm.itemsPerPage;  // Number of entries showed per page.
        var pageNumber = start/number+1;

        service.getEventPage(start, number, pageNumber, tableState, $scope.selected, sorting).then(function (result) {
            vm.displayed = result.data;
            tableState.pagination.numberOfPages = result.numberOfPages;//set the number of pages so the pagination can update
            $scope.tableState = tableState;
            $scope.eventLoading = false;
            $scope.initLoad = false;
        });
    };

}]);
