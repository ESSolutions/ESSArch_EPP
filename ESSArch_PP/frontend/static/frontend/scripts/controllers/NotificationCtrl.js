angular.module('myApp').controller('NotificationCtrl', function($scope, Notification) {
    var vm = this;

    $scope.$on('add_unseen_top_alert', function (event, data) {
        vm.alertPipe(vm.alertTableState);
    });

    vm.alertPipe = function (tableState) {
        $scope.alertLoading = true;
        if (!angular.isUndefined(tableState)) {
            var search = "";
            if (tableState.search.predicateObject) {
                var search = tableState.search.predicateObject["$"];
            }
            var sorting = tableState.sort;
            var sortString = sorting.predicate;
            if (sorting.reverse) {
                sortString = "-" + sortString;
            }
            var pagination = tableState.pagination;
            var start = pagination.start || 0;     // This is NOT the page number, but the index of item in the list that you want to use to display the table.
            var number = pagination.number || vm.alertsPerPage;  // Number of entries showed per page.
            var pageNumber = start / number + 1 || 1;
            Notification.getNotifications(pageNumber, number, sortString, search).then(function (response) {
                tableState.pagination.numberOfPages = Math.ceil(response.count / number);//set the number of pages so the pagination can update
                vm.alertTableState = tableState;
                vm.alerts = response.data;
                $scope.alertLoading = false;
            })
        }
    }
    vm.removeNotification = function(notification) {
        Notification.remove(notification.id).then(function(response) {
            vm.alertPipe(vm.alertTableState);
        });
    }
})
