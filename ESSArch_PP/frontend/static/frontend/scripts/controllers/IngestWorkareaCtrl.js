angular.module('myApp').controller('IngestWorkareaCtrl', function($scope, $controller, $translate, $rootScope) {
    var vm = this;
    $controller('BaseCtrl', { $scope: $scope });
    //context menu data
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
