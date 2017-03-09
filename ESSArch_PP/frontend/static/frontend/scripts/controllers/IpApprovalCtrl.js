angular.module('myApp').controller('IpApprovalCtrl', function($scope, $controller, $rootScope, Resource, $interval, $timeout, appConfig, $cookies, $anchorScroll, $translate, listViewService, $http, $q) {
    var vm = this;
    $controller('BaseCtrl', { $scope: $scope });
    var ipSortString = "Received,Preserving";
    vm.itemsPerPage = $cookies.get('epp-ips-per-page') || 10;
    vm.ipViewType = $cookies.get('ip-view-type') || 1;
    //Request form data
    vm.request = {
        type: "",
        purpose: "Preservation",
        storageMedium: {
            value: "",
            options: ["Disk", "Tape(type1)", "Tape(type2)"]
        }
    };
    $scope.preserveIp = function(ip) {
        listViewService.preserveIp(ip, vm.request).then(function(result) {
            $scope.requestForm = false;
            $scope.eventlog = false;
            $scope.getListViewData();
        });
    }
    //Cancel update intervals on state change
    $rootScope.$on('$stateChangeStart', function() {
        $interval.cancel(stateInterval);
        $interval.cancel(listViewInterval);
    });
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
            Resource.getIpPage(start, number, pageNumber, tableState, $scope.selectedIp, sorting, search, ipSortString, $scope.expandedAics).then(function (result) {

                for(j=0; j<ctrl.displayedIps.length; j++){
                    var aicExists = false;
                    result.data.forEach(function(b, indexb, arrayb) {
                        if(ctrl.displayedIps[j].ObjectIdentifierValue == b.ObjectIdentifierValue) {
                            aicExists = true;
                            if(!ctrl.displayedIps[j].collapsed) {
                                var tempj = j;
                                Promise.all(b.information_packages).then(function(data){
                                    var tempArray = [];
                                    for(i = 0; i < ctrl.displayedIps[tempj].information_packages.length; i++) {
                                        var ipExists = false;
                                        data.forEach(function(ip_b, indexd, arrayd) {
                                            if(ctrl.displayedIps[tempj].information_packages[i].ObjectIdentifierValue === ip_b.ObjectIdentifierValue) {
                                                ipExists = true;
                                                ctrl.displayedIps[tempj].information_packages[i].Responsible = ip_b.Responsible;
                                                ctrl.displayedIps[tempj].information_packages[i].CreateDate = ip_b.CreateDate;
                                                ctrl.displayedIps[tempj].information_packages[i].State = ip_b.State;
                                                ctrl.displayedIps[tempj].information_packages[i].step_state = ip_b.step_state;
                                                ctrl.displayedIps[tempj].information_packages[i].status = ip_b.status;
                                                arrayd.splice(indexd,1);
                                            }
                                        });
                                        if(!ipExists) {
                                            ctrl.displayedIps[tempj].information_packages.splice(i,1);
                                            i--;
                                        }
                                    }
                                    data.forEach(function(ip_b) {
                                        ctrl.displayedIps[tempj].information_packages.push(ip_b);
                                    });
                                });
                            } else {
                                ctrl.displayedIps[j].information_packages = b.information_packages;
                                b.information_packages = [];
                            }
                            ctrl.displayedIps[j].Responsible = b.Responsible;
                            ctrl.displayedIps[j].CreateDate = b.CreateDate;
                            ctrl.displayedIps[j].State = b.State;
                            ctrl.displayedIps[j].step_state = b.step_state;
                            ctrl.displayedIps[j].status = b.status;
                            arrayb.splice(indexb, 1);
                        }
                    });
                    if(!aicExists) {
                        ctrl.displayedIps.splice(j, 1);
                        j--;
                    }
                }
                result.data.forEach(function(b) {
                    ctrl.displayedIps.push(b);
                });
                tableState.pagination.numberOfPages = result.numberOfPages;//set the number of pages so the pagination can update
                $scope.ipLoading = false;
                $scope.initLoad = false;
            });
        }
    };
    //Make ip selected and add class to visualize
    $scope.selectIp = function(row) {
        vm.displayedIps.forEach(function(ip) {
            if(ip.ObjectIdentifierValue == $scope.selectedIp.ObjectIdentifierValue){
                ip.class = "";
            }
            ip.information_packages.forEach(function(subIp) {
                if(subIp.ObjectIdentifierValue == $scope.selectedIp.ObjectIdentifierValue) {
                    subIp.class = "";
                }
            });
        });
        if(row.ObjectIdentifierValue == $scope.selectedIp.ObjectIdentifierValue){
            $scope.selectedIp = {ObjectIdentifierValue: "", class: ""};
        } else {
            row.class = "selected";
            $scope.selectedIp = row;
        }
    };
    //Get data for list view
    $scope.getListViewData = function() {
        vm.callServer($scope.tableState);
        $rootScope.loadTags();
    };
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

    //Click function for Ip table
    $scope.ipTableClick = function(row) {
        if(row.package_type == 1) {
            $scope.select = false;
            $scope.eventlog = false;
            $scope.edit = false;
            $scope.eventShow = false;
            $scope.requestForm = false;

            return;
        }
        if($scope.select && $scope.ip.id== row.id){
            $scope.select = false;
            $scope.eventlog = false;
            $scope.edit = false;
            $scope.eventShow = false;
            $scope.requestForm = false;
        } else {
            $scope.ip = row;
            $rootScope.ip = $scope.ip;
            $scope.select = true;
            $scope.eventlog = true;
            $scope.edit = true;
            $scope.requestForm = true;
            $scope.eventsClick(row);
            $timeout(function() {
                $anchorScroll("request-form");
            }, 0);
        }
        $scope.statusShow = false;
    };
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
    $scope.expandedAics = [];
    $scope.expandAic = function(row) {
        row.collapsed = !row.collapsed;
        if(!row.collapsed) {
            $scope.expandedAics.push(row.ObjectIdentifierValue);
        } else {
            $scope.expandedAics.forEach(function(aic, index, array) {
                if(aic == row.ObjectIdentifierValue) {
                   $scope.expandedAics.splice(index,1);
                }
            });
        }
        row.information_packages.forEach(function(ip, index, array) {
            if(!ip.ObjectIdentifierValue) {
                $http({
                    method: 'GET',
                    url: ip
                }).then(function(response) {
                    array[index] = response.data;
                })
            }
        });
    }
    $scope.colspan = 10;
    $scope.stepTaskInfoShow = false;
    $scope.statusShow = false;
    $scope.eventShow = false;
    $scope.select = false;
    $scope.subSelect = false;
    $scope.edit = false;
    $scope.eventlog = false;
    $scope.requestForm = false;
});
