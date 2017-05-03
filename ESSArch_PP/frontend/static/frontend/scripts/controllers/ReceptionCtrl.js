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

angular.module('myApp').controller('ReceptionCtrl', function ($log, $uibModal, $timeout, $scope, $window, $location, $sce, $http, myService, appConfig, $state, $stateParams, $rootScope, listViewService, $interval, Resource, $translate, $cookies, $cookieStore, $filter, $anchorScroll, PermPermissionStore, $q, $controller){
    $controller('BaseCtrl', { $scope: $scope });
    var vm = this;
    var ipSortString = "";
    $scope.includedIps = [];
    $scope.colspan = 10;
    vm.itemsPerPage = $cookies.get('epp-ips-per-page') || 10;
    //Cancel update intervals on state change
    
    //Request form data
    function initRequestData() {
        vm.request = {
            type: "receive",
            purpose: "",
            archivePolicy: {
                value: null,
                options: []
            },
            tags: {
                value: [],
                options: []
            },
            informationClass: null,
            allowUnknownFiles: false
        };
    }
    initRequestData();
    $rootScope.$on('$stateChangeStart', function() {
        $interval.cancel(stateInterval);
        $interval.cancel(listViewInterval);
    });
    $scope.includeIp = function(row) {
        var temp = true;
        $scope.includedIps.forEach(function(included, index, array) {
            
            if(included.id == row.id) {
                $scope.includedIps.splice(index, 1);
                temp = false;
                $scope.checkMatch();
            }
        });
        if(temp) {
            $scope.includedIps.push(row);
            $scope.checkMatch();
            
        }
        if($scope.includedIps.length == 0) {
            initRequestData();
            $scope.requestForm = false;
        } else {
            if(!$scope.requestForm) {
                $scope.getArchivePolicies().then(function(result) {
                    vm.request.archivePolicy.options = result;
                    $scope.getTags().then(function(result) {
                        vm.request.tags.options = result;
                        $scope.requestForm = true;
                    });
                });
            }
        }
    }
    $scope.archivePolicyChange = function() {
        vm.request.informationClass = vm.request.archivePolicy.value.information_class;
        $scope.checkMatch();
    }
    $scope.checkMatch = function() {
        if(vm.request.archivePolicy.value != null) {
            for(i=0;i<$scope.includedIps.length; i++) {
                    if(vm.request.archivePolicy.value.information_class != $scope.includedIps[i].information_class) {
                        $scope.informationClassAlert = $scope.alerts.matchError;
                        $scope.informationClassAlert.message = $scope.alerts.matchError.msg + $scope.includedIps[i].id;
                        break;
                    }
                    $scope.informationClassAlert = null;
                };
        }
    };
    // Click funtion columns that does not have a relevant click function
    $scope.ipRowClick = function(row) {
        $scope.selectIp(row);
        if($scope.ip == row){
            row.class = "";
            $scope.selectedIp = {id: "", class: ""};
        }
        if($scope.eventShow) {
            $scope.eventsClick(row);
        }
        if($scope.statusShow) {
            $scope.stateClicked(row);
        }
        if ($scope.select) {
            $scope.ipTableClick(row);
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
    //If status view is visible, start update interval
    $scope.$watch(function(){return $scope.statusShow;}, function(newValue, oldValue) {
        if(newValue) {
            $interval.cancel(stateInterval);
            stateInterval = $interval(function(){$scope.statusViewUpdate($scope.ip)}, appConfig.stateInterval);
        } else {
            $interval.cancel(stateInterval);
        }
    });
    //Get data for status view
    
    /*******************************************/
    /*Piping and Pagination for List-view table*/
    /*******************************************/
    
    var ctrl = this;
    $scope.selectedIp = {id: "", class: ""};
    $scope.selectedProfileRow = {profile_type: "", class: ""};
    this.displayedIps = [];
    //Get data according to ip table settings and populates ip table
    this.callServer = function callServer(tableState) {
        $scope.ipLoading = true;
        if(vm.displayedIps.length == 0) {
            $scope.initLoad = true;
        }
        if(!angular.isUndefined(tableState)) {
            $scope.tableState = tableState;
            var search = "";
            if(tableState.search.predicateObject) {
                var search = tableState.search.predicateObject["$"];
            }
            var sorting = tableState.sort;
            var pagination = tableState.pagination;
            var start = pagination.start || 0;     // This is NOT the page number, but the index of item in the list that you want to use to display the table.
            var number = pagination.number || vm.itemsPerPage;  // Number of entries showed per page.
            var pageNumber = start/number+1;
            Resource.getReceptionPage(start, number, pageNumber, tableState, $scope.selectedIp, $scope.includedIps, sorting, search, ipSortString, $scope.columnFilters).then(function (result) {
                ctrl.displayedIps = result.data;
                tableState.pagination.numberOfPages = result.numberOfPages;//set the number of pages so the pagination can update
                $scope.ipLoading = false;
                $scope.initLoad = false;
            });
        }
    };
    //Make ip selected and add class to visualize
    $scope.selectIp = function(row) {
        vm.displayedIps.forEach(function(ip) {
            if(ip.id == $scope.selectedIp.id){
                ip.class = "";
            }
        });
        if(row.id == $scope.selectedIp.id){
            $scope.selectedIp = {id: "", class: ""};
        } else {
            row.class = "selected";
            $scope.selectedIp = row;
        }
    };
    
    //Click function for Ip table
    $scope.ipTableClick = function(row) {
        if($scope.select && $scope.ip.id== row.id){
        } else {
            $scope.ip = row;
            $rootScope.ip = $scope.ip;
        }
    };
    $scope.$watch(function(){return $rootScope.navigationFilter;}, function(newValue, oldValue) {
        $scope.getListViewData();
    }, true);
    //Click funciton for event view
    $scope.eventsClick = function (row) {
        if($scope.eventShow && $scope.ip == row){
            $scope.eventShow = false;
            $rootScope.stCtrl = null;
        } else {
            if($rootScope.stCtrl) {
                $rootScope.stCtrl.pipe();
            }
            getEventlogData();
            $scope.eventShow = true;
            $scope.statusShow = false;
        }
        $scope.select = false;
        $scope.edit = false;
        $scope.eventlog = false;
        $scope.ip = row;
        $rootScope.ip = row;
    };
    
    //Adds a new event to the database
    $scope.addEvent = function(ip, eventType, eventDetail) {
        listViewService.addEvent(ip, eventType, eventDetail).then(function(value) {
        });
    }
    //Get data for list view
    $scope.getListViewData = function() {
        vm.callServer($scope.tableState);
        $rootScope.loadTags();
    };
    // Progress bar max value
    $scope.max = 100;
    vm.options = {};
    //Click funciton for profile view
    //Get data for eventlog view
    function getEventlogData() {
        listViewService.getEventlogData().then(function(value){
            $scope.eventTypeCollection = value;
        });
    };
    //Decides visibility of stepTask info page
    $scope.stepTaskInfoShow = false;
    //Decides visibility of status view
    $scope.statusShow = false;
    //Decides visibility of events view
    $scope.eventShow = false;
    //Decides visibility of select view
    $scope.select = false;
    //Decides visibility of sub-select view
    $scope.subSelect = false;
    //Decides visibility of edit view
    $scope.edit = false;
    //Decides visibility of eventlog view
    $scope.eventlog = false;
    $scope.requestForm = false;
    //Html popover template for currently disabled
    $scope.htmlPopover = $sce.trustAsHtml('<font size="3" color="red">Currently disabled</font>');
    
    //Toggle visibility of select view
    $scope.toggleSelectView = function () {
        if($scope.select == false){
            $scope.select = true;
        } else {
            $scope.select = false;
        }
    };
    //Toggle visibility of sub-select view
    $scope.toggleSubSelectView = function () {
        if($scope.subSelect == false){
            $scope.subSelect = true;
        } else {
            $scope.subSelect = false;
        }
    };
    //Toggle visibility of edit view
    $scope.toggleEditView = function () {
        if($scope.edit == false){
            $('.edit-view').show();
            $scope.edit = true;
            $scope.eventlog = true;
        } else {
            $('.edit-view').hide();
            $scope.edit = false;
            $scope.eventlog = false;
        }
    };
    //Toggle visibility of eventlog view
    $scope.toggleEventlogView = function() {
        if($scope.eventlog == false){
            $scope.eventlog = true;
        }else {
            $scope.eventlog = false;
        }
    }
    //Remove ip
    $scope.removeIp = function (ipObject) {
        $http({
            method: 'DELETE',
            url: ipObject.url
        }).then(function() {
            vm.displayedIps.splice(vm.displayedIps.indexOf(ipObject), 1);
            $scope.edit = false;
            $scope.select = false;
            $scope.eventlog = false;
            $scope.eventShow = false;
            $scope.statusShow = false;
        });
    }
    //Update ip list view with an interval
    //Update only if status < 100 and no step has failed in any IP
    var listViewInterval;
    function updateListViewConditional() {
        $interval.cancel(listViewInterval);
        listViewInterval = $interval(function() {
            var updateVar = false;
            vm.displayedIps.forEach(function(ip, idx) {
                if(ip.status < 100) {
                    if(ip.step_state != "FAILURE") {
                        updateVar = true;
                    }
                }
            });
            if(updateVar) {
                $scope.getListViewData();
            } else {
                $interval.cancel(listViewInterval);
                listViewInterval = $interval(function() {
                    var updateVar = false;
                    vm.displayedIps.forEach(function(ip, idx) {
                        if(ip.status < 100) {
                            if(ip.step_state != "FAILURE") {
                                updateVar = true;
                            }
                        }
                    });
                    if(!updateVar) {
                        $scope.getListViewData();
                    } else {
                        updateListViewConditional();
                    }
                    
                }, appConfig.ipIdleInterval);
            }
        }, appConfig.ipInterval);
    };
    updateListViewConditional();
    
    //Reload current view
    $scope.reloadPage = function (){
        $state.reload();
    }
    $scope.yes = $translate.instant('YES');
    $scope.no = $translate.instant('NO');
    vm.validatorModel = {
    };
    vm.validatorFields = [
    {
        "templateOptions": {
            "type": "text",
            "label": $translate.instant('VALIDATEFILEFORMAT'),
            "options": [{name: $scope.yes, value: true},{name: $scope.no, value: false}],
        },
        "defaultValue": true,
        "type": "select",
        "key": "validate_file_format",
    },
    {
        "templateOptions": {
            "type": "text",
            "label": $translate.instant('VALIDATEXMLFILE'),
            "options": [{name: $scope.yes, value: true},{name: $scope.no, value: false}],
        },
        "defaultValue": true,
        "type": "select",
        "key": "validate_xml_file",
    },
    {
        "templateOptions": {
            "type": "text",
            "label": $translate.instant('VALIDATELOGICALPHYSICALREPRESENTATION'),
            "options": [{name: $scope.yes, value: true},{name: $scope.no, value: false}],
        },
        "defaultValue": true,
        "type": "select",
        "key": "validate_logical_physical_representation",
    },
    {
        "templateOptions": {
            "type": "text",
            "label": $translate.instant('VALIDATEINTEGRITY'),
            "options": [{name: $scope.yes, value: true},{name: $scope.no, value: false}],
        },
        "defaultValue": true,
        "type": "select",
        "key": "validate_integrity",
    }
    ];
    
    $scope.getArchivePolicies = function() {
        return $http({
            method: 'GET',
            url: appConfig.djangoUrl + 'archive_policies/'
        }).then(function(response) {
            return response.data;
        });
    }
    $scope.getTags = function() {
        return $http({
            method: 'GET',
            url: appConfig.djangoUrl + 'tags/'
        }).then(function(response) {
            return response.data;
        });
    }
    $scope.receive = function(ips) {
        ips.forEach(function(ip) {
            $http({
                method: 'POST',
                url: appConfig.djangoUrl +'ip-reception/'+ ip.id + '/receive/',
                data: {
                    archive_policy: vm.request.archivePolicy.value.id,
                    purpose: vm.request.purpose,
                    tags: vm.request.tags.value.map(function(tag){return tag.id}),
                    allow_unknown_files: vm.request.allowUnknownFiles
                }
            }).then(function(){
                $scope.getListViewData();
                $scope.eventlog = false;
                $scope.edit = false;
                $scope.requestForm = false;
                initRequestData();
            });
        });
    }
    $scope.removeIp = function (ipObject) {
        $http({
            method: 'DELETE',
            url: ipObject.url
        }).then(function() {
            vm.displayedIps.splice(vm.displayedIps.indexOf(ipObject), 1);
            $scope.edit = false;
            $scope.select = false;
            $scope.eventlog = false;
            $scope.eventShow = false;
            $scope.statusShow = false;
        });
    }
    $scope.informationClassAlert = null;
    $scope.alerts = {
        matchError: { type: 'danger', msg: $translate.instant('MATCH_ERROR') },
    };
    $scope.closeAlert = function() {
        $scope.informationClassAlert = null;
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
