angular.module('myApp').controller('MyPageCtrl', function($scope, $controller, $rootScope) {
    var vm = this;
    $scope.visibleRequests = {
        access: false,
        workarea: false,
        receive: false
    };
    $scope.tableControlCollapsed = true;
    $controller('BaseCtrl', { $scope: $scope });
    vm.displayedIps = [{
        Label: "request",
        Responsible: {username: "admin"},
        CreateDate: new Date(),
        RequestType: "Request type"
    }];
});
