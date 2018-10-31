angular.module('essarch.controllers').controller('VersionModalInstanceCtrl', function (Search, $translate, $uibModalInstance, djangoAuth, appConfig, $http, data, $scope, Notifications, $timeout, ErrorResponse) {
    var $ctrl = this;
    $ctrl.node = data.node.original;

    $ctrl.createNewVersion = function(node) {
        Search.createNewVersion(node).then(function(response) {
            Notifications.add($translate.instant('NEW_VERSION_CREATED'), 'success');
            $uibModalInstance.close("added");
        }).catch(function(response) {
            ErrorResponse.default(response);
        })
    }
    $ctrl.cancel = function() {
        $uibModalInstance.dismiss('cancel');
    }
});
