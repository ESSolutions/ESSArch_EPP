angular.module('myApp').controller('AccessWorkareaCtrl', function($scope, $controller, $translate, $rootScope, $state) {
    $controller('BaseCtrl', { $scope: $scope });
    var vm = this;
    $scope.menuOptions = [
        [$translate.instant('APPLYCHANGES'), function ($itemScope, $event, modelValue, text, $li) {
            console.log($itemScope.row);
        }],
        [$translate.instant('Create DIP'), function ($itemScope, $event, modelValue, text, $li) {
            $scope.gotoCreateDip($itemScope.row);
        }],

    ];
    $scope.gotoCreateDip = function(ip) {
        $state.go('home.access.createDip', {ip: ip});
    }
    vm.displayedIps = [{
        id: "asdasdas324234234dsgsdgsg",
        Label: "test",
        Responsible: {username: $rootScope.auth.username},
        CreateDate: new Date(),
        ArchivistOrganization: "The test archivist",
        State: "Test IP",
        status: 100,
    }];

});
