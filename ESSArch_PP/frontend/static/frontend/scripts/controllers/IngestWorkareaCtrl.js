angular.module('myApp').controller('IngestWorkareaCtrl', function($scope, $controller, $rootScope, Resource, $interval, $timeout, appConfig, $cookies, $anchorScroll, $translate, $http, listViewService, Requests) {
    var vm = this;
    var ipSortString = "Accessed";
    $controller('BaseCtrl', { $scope: $scope, vm: vm, ipSortString: ipSortString });
    //context menu data
    $scope.menuOptions = function() {
        return [];
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
            $scope.filebrowser = false;
            $scope.initRequestData();
            $scope.getListViewData();
        });
    }

    /*******************************************/
    /*Piping and Pagination for List-view table*/
    /*******************************************/

    $scope.expandedAics = [];
    $scope.selectedProfileRow = {profile_type: "", class: ""};
    vm.displayedIps = [];
    //Get data according to ip table settings and populates ip table
    vm.callServer = function callServer(tableState) {
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
				vm.displayedIps = result.data;
				tableState.pagination.numberOfPages = result.numberOfPages;//set the number of pages so the pagination can update
				$scope.ipLoading = false;
				$scope.initLoad = false;
			});
        }
    };

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
});
