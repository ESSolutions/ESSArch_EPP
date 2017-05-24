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

angular.module('myApp').controller('MediaInformationCtrl', function($scope, $rootScope, $controller, $cookies, $http, appConfig, Resource, $interval, $anchorScroll, $timeout) {
    var vm = this;
    $controller('BaseCtrl', { $scope: $scope });
    $scope.colspan = 6;
    $scope.selectedStorageMedium = {id: "", class: ""};
    vm.storageObjects = [];
    $scope.select = false;
    vm.objectsPerPage = 10;
    $scope.getStorageObjects = function(medium) {
        $http({
            method: "GET",
            url: medium.url + 'storage-objects/',
        }).then(function(response) {
            vm.storageObjects = response.data;
        });
    }
    $scope.selectObject = function(row) {
        vm.storageObjects.forEach(function(object) {
            if(object.id == $scope.selectedObject.id){
                object.class = "";
            }
        });
    }
    $scope.storageMediumTableClick = function(row) {
        if($scope.select && $scope.storageMedium.id == row.id){
            $scope.select = false;
            $scope.eventlog = false;
            $scope.edit = false;
            $scope.eventShow = false;
        } else {
            $scope.storageMedium = row;
            $rootScope.storageMedium = row;
            //$scope.getStorageObjects(row);
            $scope.select = true;
            $scope.eventlog = true;
            $scope.edit = true;
        }
        $scope.statusShow = false;
    };
    //Cancel update intervals on state change
    $rootScope.$on('$stateChangeStart', function() {
        $interval.cancel(stateInterval);
        $interval.cancel(listViewInterval);
    });
    // Click funtion columns that does not have a relevant click function
    $scope.storageRowClick = function(row) {
        $scope.selectStorageMedium(row);
        if($scope.ip == row){
            row.class = "";
            $scope.selectedStorageMedium = {id: "", class: ""};
        }
        if($scope.eventShow) {
            $scope.eventsClick(row);
        }
        if($scope.statusShow) {
            $scope.stateClicked(row);
        }
        if ($scope.select) {
            $scope.storageMediumTableClick(row);
        }
    }
    //Click function for status view
    var stateInterval;
    $scope.stateClicked = function(row){
        if($scope.statusShow && $scope.ip == row){
            $scope.statusShow = false;
        } else {
            $scope.statusShow = true;
            $scope.edit = false;
            $scope.statusViewUpdate(row);
        }
        $scope.subSelect = false;
        $scope.eventlog = false;
        $scope.select = false;
        $scope.eventShow = false;
        $scope.ip = row;
        $rootScope.ip = row;
    };

    //Click funciton for event view
    $scope.eventsClick = function (row) {
        if($scope.eventShow && $scope.ip == row){
            $scope.eventShow = false;
            $rootScope.stCtrl = null;
        } else {
            if($rootScope.stCtrl) {
                $rootScope.stCtrl.pipe();
            }
            $scope.eventShow = true;
            $scope.statusShow = false;
        }
        $scope.ip = row;
        $rootScope.ip = row;
    };
    //If status view is visible, start update interval
    $scope.$watch(function(){return $scope.statusShow;}, function(newValue, oldValue) {
        if(newValue) {
            $interval.cancel(stateInterval);
            stateInterval = $interval(function(){$scope.statusViewUpdate($scope.ip)}, appConfig.stateInterval);
        } else {
            $interval.cancel(stateInterval);
        }
    });
    $scope.$watch(function(){return $rootScope.ipUrl;}, function(newValue, oldValue) {
        $scope.getListViewData();
    }, true);

    $scope.updateStorageMediums = function() {
        vm.callServer($scope.mediumTableState);
    }
    /*******************************************/
    /*Piping and Pagination for List-view table*/
    /*******************************************/
    var ctrl = this;
    $scope.selectedStorageMethod = {id: "", class: ""};
    this.displayedMediums = [];
    //Get data according to ip table settings and populates ip table
    this.callServer = function callServer(tableState) {
        $scope.ipLoading = true;
        if(vm.displayedMediums.length == 0) {
            $scope.initLoad = true;
        }
        if(!angular.isUndefined(tableState)) {
            $scope.mediumTableState = tableState;
            var search = "";
            if(tableState.search.predicateObject) {
                var search = tableState.search.predicateObject["$"];
            }
            var sorting = tableState.sort;
            var pagination = tableState.pagination;
            var start = pagination.start || 0;     // This is NOT the page number, but the index of item in the list that you want to use to display the table.
            var number = pagination.number || vm.itemsPerPage;  // Number of entries showed per page.
            var pageNumber = start/number+1;
            Resource.getStorageMediums(start, number, pageNumber, tableState, $scope.selectedStorageMedium, sorting, search).then(function (result) {
                ctrl.displayedMediums = result.data;
                tableState.pagination.numberOfPages = result.numberOfPages;//set the number of pages so the pagination can update
                $scope.ipLoading = false;
                $scope.initLoad = false;
            });
        }
    };
    this.objectPipe = function objectPipe(tableState) {
        $scope.objectLoading = true;
        if(vm.storageObjects.length == 0) {
            $scope.initObjLoad = true;
        }
        if(!angular.isUndefined(tableState)) {
            $scope.objectTableState = tableState;
            var search = "";
            if(tableState.search.predicateObject) {
                var search = tableState.search.predicateObject["$"];
            }
            var sorting = tableState.sort;
            var pagination = tableState.pagination;
            var start = pagination.start || 0;     // This is NOT the page number, but the index of item in the list that you want to use to display the table.
            var number = pagination.number || vm.objectsPerPage;  // Number of entries showed per page.
            var pageNumber = start/number+1;
            Resource.getStorageObjects(start, number, pageNumber, tableState, $scope.storageMedium, sorting, search).then(function (result) {
                ctrl.storageObjects = result.data;
                tableState.pagination.numberOfPages = result.numberOfPages;//set the number of pages so the pagination can update
                $scope.objectLoading = false;
                $scope.initObjLoad = false;
            });
        }
    };
    //Make ip selected and add class to visualize
    $scope.selectStorageMedium = function(row) {
        vm.displayedMediums.forEach(function(method) {
            if(method.id == $scope.selectedStorageMedium.id){
                method.class = "";
            }
        });
        if(row.id == $scope.selectedStorageMedium.id){
            $scope.selectedStorageMedium = {id: "", class: ""};
        } else {
            row.class = "selected";
            $scope.selectedStorageMedium = row;
        }
    };
    //Get data for list view
    $scope.getListViewData = function() {
        vm.callServer($scope.tableState);
        $rootScope.loadTags();
    };
    var listViewInterval;
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
