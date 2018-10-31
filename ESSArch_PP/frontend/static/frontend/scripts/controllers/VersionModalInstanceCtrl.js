angular.module('essarch.controllers').controller('VersionModalInstanceCtrl', function (Search, $translate, $uibModalInstance, djangoAuth, appConfig, $http, data, $scope, Notifications, $timeout) {
    var $ctrl = this;
    $ctrl.node = data.node.original;

    $ctrl.createNewVersion = function(node) {
        Search.createNewVersion(node).then(function(response) {
            Notifications.add($translate.instant('NEW_VERSION_CREATED'), 'success');
            $uibModalInstance.close("added");
        }).catch(function(response) {
            if(![401, 403, 500, 503].includes(response.status)) {
                if(response.data && response.data.detail) {
                    Notifications.add(response.data.detail, "error");
                } else {
                    Notifications.add($translate('UNKNOWN_ERROR'), 'error')
                }
            }
        })
    }
    $ctrl.cancel = function() {
        $uibModalInstance.dismiss('cancel');
    }
});
