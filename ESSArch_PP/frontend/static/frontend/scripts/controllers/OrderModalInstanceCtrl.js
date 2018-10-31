angular.module('essarch.controllers').controller('OrderModalInstanceCtrl', function ($uibModalInstance, data, $http, Notifications, appConfig, listViewService, $translate) {
    var $ctrl = this;
    if(data) {
        $ctrl.data = data;
    }
    $ctrl.newOrder = function(label) {
        $ctrl.creatingOrder = true;
        listViewService.prepareOrder(label).then(function(result) {
            $ctrl.creatingOrder = false;
            $uibModalInstance.close();
        }).catch(function(response) {
            $ctrl.creatingOrder = false;
            if(![401, 403, 500, 503].includes(response.status)) {
                if(response.data && response.data.detail) {
                    Notifications.add(response.data.detail, "error");
                } else {
                    Notifications.add($translate('UNKNOWN_ERROR'), 'error')
                }
            }
        });
    };
    $ctrl.remove = function (order) {
        $ctrl.removing = true;
        console.log(order)
        $http({
            method: 'DELETE',
            url: appConfig.djangoUrl + 'orders/' + order.id + '/'
        }).then(function() {
            $ctrl.removing = false;
            $uibModalInstance.close();
        }).catch(function() {
            $ctrl.removing = false;
    })
    };
    $ctrl.ok = function() {
        $uibModalInstance.close();
    }
    $ctrl.cancel = function () {
        $uibModalInstance.dismiss('cancel');
    };
});
