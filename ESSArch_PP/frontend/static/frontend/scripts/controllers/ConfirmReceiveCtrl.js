angular.module('essarch.controllers').controller('ConfirmReceiveCtrl', function (IPReception, Notifications, $uibModalInstance, data, $scope, $controller, $translate) {
    var $ctrl = this;

    $ctrl.receiving = false;
    if(data) {
        $ctrl.data = data;
    }
    $ctrl.receive = function (ip) {
        $ctrl.receiving = true;
        return IPReception.receive({
            id: ip.id,
            archive_policy: data.request.archivePolicy.value.id,
            purpose: data.request.purpose,
            tag: data.tag,
            allow_unknown_files: data.request.allowUnknownFiles,
            validators: data.validatorModel
        }).$promise.then(function (response) {
            Notifications.add(response.detail, "success", 3000);
            $ctrl.data = { received: true, status: "received" };
            $ctrl.receiving = false;
            $uibModalInstance.close($ctrl.data);
        }).catch(function (response) {
            $ctrl.receiving = false;
            $ctrl.data = { received: false, status: "error" };
            if(![401, 403, 500, 503].includes(response.status)) {
                if(response.data && response.data.detail) {
                    Notifications.add(response.data.detail, "error");
                } else {
                    Notifications.add($translate('UNKNOWN_ERROR'), 'error')
                }
            }
            $uibModalInstance.dismiss($ctrl.data);
        })
    };
    $ctrl.cancel = function () {
        $uibModalInstance.dismiss('cancel');
    };
})
