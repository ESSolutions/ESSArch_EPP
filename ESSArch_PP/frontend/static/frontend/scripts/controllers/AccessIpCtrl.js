angular.module('myApp').controller('AccessIpCtrl', function($scope, $controller, $rootScope) {
    var vm = this;
    $controller('BaseCtrl', { $scope: $scope });
    vm.request = {
        type: "preserve_ip",
        purpose: "Preservation",
        storageMedium: {
            value: "",
            options: ["Disk", "Tape(type1)", "Tape(type2)"]
        }
    };
    vm.displayedIps = [{
        Label: "test",
        Responsible: {username: $rootScope.auth.username},
        CreateDate: new Date(),
        State: "Test IP",
        status: 100,
    }];

});
