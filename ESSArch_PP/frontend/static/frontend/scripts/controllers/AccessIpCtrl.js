angular.module('myApp').controller('AccessIpCtrl', function($scope, $controller, $rootScope, Resource, $interval, $timeout, appConfig, $cookies, $anchorScroll, $translate, $http, $state) {
    var vm = this;
    $controller('BaseCtrl', { $scope: $scope });
    var ipSortString = "";
    vm.itemsPerPage = $cookies.get('epp-ips-per-page') || 10;
    //Request form data
    $scope.initRequestData = function () {
        vm.request = {
            type: "",
            purpose: "",
            storageMedium: {
                value: "",
                options: ["Disk", "Tape(type1)", "Tape(type2)"]
            }
        };
    }
    $scope.initRequestData();

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
            var archived = true;
            Resource.getIpPage(start, number, pageNumber, tableState, $scope.selectedIp, sorting, search, ipSortString, $scope.expandedAics, $scope.columnFilters, archived).then(function (result) {
                ctrl.displayedIps = result.data;
                tableState.pagination.numberOfPages = result.numberOfPages;//set the number of pages so the pagination can update
                $scope.ipLoading = false;
                $scope.initLoad = false;
            });
        }
    };
    $scope.accessIp = function(ip, request) {
        var data = { purpose: request.purpose, tar: request.type === "view_tar", extracted: request.type === "view"};
        $http.post(ip.url + "access/", data).then(function(response) {
            $scope.edit = false;
            $scope.select = false;
            $scope.initRequestData();
            $timeOut(function() {
                $scope.getListViewData();
            });
        });
    }
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
            $scope.requestForm = false;
        } else {
            $scope.ip = row;
            $rootScope.ip = $scope.ip;
            $scope.select = true;
            $scope.eventlog = true;
            $scope.edit = true;
            $scope.requestForm = true;
        }
        $scope.eventShow = false;
        $scope.statusShow = false;
    };
    $scope.colspan = 9;
    $scope.stepTaskInfoShow = false;
    $scope.statusShow = false;
    $scope.eventShow = false;
    $scope.select = false;
    $scope.subSelect = false;
    $scope.edit = false;
    $scope.eventlog = false;
    $scope.requestForm = false;

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
