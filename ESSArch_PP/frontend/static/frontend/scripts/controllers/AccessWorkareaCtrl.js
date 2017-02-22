angular.module('myApp').controller('AccessWorkareaCtrl', function($scope, $controller, $translate, $rootScope) {
    $controller('BaseCtrl', { $scope: $scope });
    var vm = this;
    $scope.menuOptions = [
        [$translate.instant('APPLYCHANGES'), function ($itemScope, $event, modelValue, text, $li) {
            console.log($itemScope);
        }],
    ];
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
