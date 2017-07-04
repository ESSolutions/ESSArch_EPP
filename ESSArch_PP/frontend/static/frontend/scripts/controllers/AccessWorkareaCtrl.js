angular.module('myApp').controller('AccessWorkareaCtrl', function($scope, $controller, $rootScope, Resource, $interval, $timeout, appConfig, $cookies, $anchorScroll, $translate, $state, $http, listViewService, Requests) {
    var vm = this;
    var ipSortString = "Accessed";
    $controller('BaseCtrl', { $scope: $scope, vm: vm, ipSortString: ipSortString });

    $scope.menuOptions = function() {
        return [
            [$translate.instant('APPLYCHANGES'), function ($itemScope, $event, modelValue, text, $li) {
                console.log($itemScope.row);
            }],
        ];
    }

    /*******************************************/
    /*Piping and Pagination for List-view table*/
    /*******************************************/

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
			Resource.getWorkareaIps("access", start, number, pageNumber, tableState, sorting, search, $scope.expandedAics, $scope.columnFilters).then(function (result) {
				vm.displayedIps = result.data;
				tableState.pagination.numberOfPages = result.numberOfPages;//set the number of pages so the pagination can update
				$scope.ipLoading = false;
				$scope.initLoad = false;
			});

            /*Resource.getIpPage(start, number, pageNumber, tableState, $scope.selectedIp, sorting, search, ipSortString).then(function (result) {
                ctrl.displayedIps = result.data;
                tableState.pagination.numberOfPages = result.numberOfPages;//set the number of pages so the pagination can update
                $scope.ipLoading = false;
                $scope.initLoad = false;
            });*/
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
			$scope.initRequestData();
			if ($scope.ip != null && $scope.ip.object_identifier_value== row.object_identifier_value) {
				$scope.ip = null;
				$rootScope.ip = null;
                $scope.filebrowser = false;
			} else {
				$scope.ip = row;
				$rootScope.ip = $scope.ip;
			}
			return;
		}
        if($scope.select && $scope.ip.object_identifier_value == row.object_identifier_value){
            $scope.select = false;
            $scope.eventlog = false;
            $scope.edit = false;
            $scope.eventShow = false;
            $scope.requestForm = false;
            $scope.ip = null;
            $rootScope.ip = null;
            $scope.filebrowser = false;
            $scope.initRequestData();
        } else {
            $scope.select = true;
            $scope.eventlog = true;
            $scope.edit = true;
            $scope.requestForm = true;
            if (!$scope.eventsShow || $scope.ip.object_identifier_value != row.object_identifier_value) {
                $scope.eventShow = false;
                $scope.eventsClick(row);
            };
            $scope.ip = row;
            $rootScope.ip = $scope.ip;
        }
        $scope.statusShow = false;
    };
});
