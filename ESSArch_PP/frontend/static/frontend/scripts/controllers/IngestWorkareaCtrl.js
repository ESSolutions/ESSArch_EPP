angular.module('myApp').controller('IngestWorkareaCtrl', function($scope, $controller, $rootScope, Resource, $interval, $timeout, appConfig, $cookies, $anchorScroll, $translate, $http, listViewService, Requests) {
    var vm = this;
    $controller('BaseCtrl', { $scope: $scope });
    var ipSortString = "Accessed";
    $scope.ip = null;
    $rootScope.ip = null;
    vm.itemsPerPage = $cookies.get('epp-ips-per-page') || 10;
    //context menu data
    $scope.menuOptions = function() {
        return [];
    }
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

    $scope.submitRequest = function (ip, request) {
        switch (request.type) {
            case "preserve":
                $scope.preserveIp(ip, request);
                break;
            case "diff_check":
                console.log("request not implemented");
                break;
            default:
                console.log("request not matched");
                break;
        }
    }
    $scope.preserveIp = function (ip, request) {
        Requests.preserve(ip, { purpose: request.purpose }).then(function (result) {
            $scope.requestForm = false;
            $scope.eventlog = false;
            $scope.eventShow = false;
            $scope.initRequestData();
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
        if($scope.ip == row){
            $scope.ip = null;
            $rootScope.ip = null;
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
    $scope.stateClicked = function (row) {
        if ($scope.statusShow) {
            $scope.tree_data = [];
            if ($scope.ip == row) {
                $scope.statusShow = false;
                $scope.ip = null;
                $rootScope.ip = null;
            } else {
                $scope.statusShow = true;
                $scope.edit = false;
                $scope.statusViewUpdate(row);
                $scope.ip = row;
                $rootScope.ip = row;
            }
        } else {
            $scope.statusShow = true;
            $scope.edit = false;
            $scope.statusViewUpdate(row);
            $scope.ip = row;
            $rootScope.ip = row;
        }
        $scope.subSelect = false;
        $scope.eventlog = false;
        $scope.select = false;
        $scope.eventShow = false;
    };
    //Click funciton for event view
	$scope.eventsClick = function (row) {
		if($scope.eventShow && $scope.ip == row){
			$scope.eventShow = false;
			$rootScope.stCtrl = null;
			if(!$scope.requestForm) {
				$scope.ip = null;
				$rootScope.ip = null;
			};
		} else {
			if($rootScope.stCtrl) {
				$rootScope.stCtrl.pipe();
			}
			$scope.eventShow = true;
			$scope.statusShow = false;
			$scope.ip = row;
			$rootScope.ip = row;
		}
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
    $scope.expandedAics = [];
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
	        Resource.getWorkareaIps("ingest", start, number, pageNumber, tableState, sorting, search, $scope.expandedAics, $scope.columnFilters).then(function (result) {
				ctrl.displayedIps = result.data;
				tableState.pagination.numberOfPages = result.numberOfPages;//set the number of pages so the pagination can update
				$scope.ipLoading = false;
				$scope.initLoad = false;
			});
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
            if ($scope.ip != null && $scope.ip.object_identifier_value == row.object_identifier_value) {
                $scope.ip = null;
                $rootScope.ip = null;
            } else {
                $scope.ip = row;
                $rootScope.ip = $scope.ip;
            }
			$scope.initRequestData();
			return;
		}
        if($scope.select && $scope.ip.id == row.id){
            $scope.select = false;
            $scope.eventlog = false;
            $scope.edit = false;
            $scope.eventShow = false;
            $scope.requestForm = false;
            $scope.ip = false;
			$rootScope.ip = false
			$scope.initRequestData();
        } else {
            $scope.ip = row;
            $rootScope.ip = $scope.ip;
            $scope.select = true;
            $scope.eventlog = true;
            $scope.edit = true;
            $scope.requestForm = true;
            if (!$scope.eventsShow || $scope.ip.object_identifier_value != row.object_identifier_value) {
                $scope.eventShow = false;
                $scope.eventsClick(row);
            }
            $scope.ip = row;
			$rootScope.ip = $scope.ip;
        }
        $scope.statusShow = false;
    };
    $scope.filebrowser = false;
    $scope.filebrowserClick = function (ip) {
        if ($scope.filebrowser && $scope.ip == ip) {
            $scope.filebrowser = false;
            $scope.ip = null;
            $rootScope.ip = null;
        } else {
            $scope.filebrowser = true;
            ip.url = appConfig.djangoUrl + "ip-reception/" + ip.id + "/";
            $scope.ip = ip;
            $rootScope.ip = ip;
        }
    }
    $scope.colspan = 9;
    $scope.stepTaskInfoShow = false;
    $scope.statusShow = false;
    $scope.eventShow = false;
    $scope.select = false;
    $scope.subSelect = false;
    $scope.edit = false;
    $scope.eventlog = false;
    $scope.requestForm = false;

    $scope.expandedAics = [];
    $scope.expandAic = function (row) {
		row.collapsed = !row.collapsed;
		if(!row.collapsed) {
			$scope.expandedAics.push(row.object_identifier_value);
		} else {
			$scope.expandedAics.forEach(function(aic, index, array) {
				if(aic == row.object_identifier_value) {
					$scope.expandedAics.splice(index,1);
				}
			});
		}
		row.information_packages.forEach(function(ip, index, array) {
			if(!ip.object_identifier_value) {
				$http({
					method: 'GET',
					url: ip
				}).then(function(response) {
					array[index] = response.data;
				})
			}
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
