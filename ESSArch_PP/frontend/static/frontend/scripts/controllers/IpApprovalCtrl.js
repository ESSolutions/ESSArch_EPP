angular.module('myApp').controller('IpApprovalCtrl', function($scope, $controller, $rootScope) {
    var vm = this;
    $controller('BaseCtrl', { $scope: $scope });
    //Request form data
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
        ArchivistOrganization: "The test archivist",
        State: "Test IP",
        status: 100,
    }];
});
