angular.module('myApp').controller('EditStructureUnitModalInstanceCtrl', function (Search, $translate, $uibModalInstance, djangoAuth, appConfig, $http, data, $scope, Notifications, $timeout, $q) {
    var $ctrl = this;
    $ctrl.editNode = {};
    $ctrl.options = {};
    $ctrl.nodeFields = [];
    $ctrl.types = [];
    $ctrl.$onInit = function() {
        if(data.node) {
            $ctrl.node = data.node;
            $ctrl.editNode = angular.copy($ctrl.node);
        }
        if(data.structure) {
            $ctrl.structure = data.structure;
        }


        $ctrl.nodeFields = [
            {
                "templateOptions": {
                    "label": $translate.instant("REFERENCE_CODE"),
                    "type": "text",
                    "focus": true
                },
                "type": "input",
                "key": "reference_code",
            },
            {
                "templateOptions": {
                    "type": "text",
                    "label": $translate.instant("NAME"),
                },
                "type": "input",
                "key": "name",
            },
            {
                "templateOptions": {
                    "label": $translate.instant("DESCRIPTION"),
                    "type": "text",
                },
                "type": "input",
                "key": "description",
            },
        ];
    }

    $ctrl.changed = function() {
        return !angular.equals($ctrl.editNode, $ctrl.node);
    }
    /**
     * update new classification structure
     */
    $ctrl.saving = false;
    $ctrl.update = function() {
        $ctrl.saving = true;
        $http({
            method: 'PATCH',
            url: appConfig.djangoUrl + 'classification-structures/' + data.structure.id + '/units/' + $ctrl.node.id + '/',
            data: $ctrl.editNode
        }).then(function(response) {
            $ctrl.saving = false;
            Notifications.add($translate.instant('NODE_EDITED'), 'success');
            $uibModalInstance.close(response.data);
        }).catch(function(response) {
            $ctrl.saving = false;
            if(response.data && response.data.detail) {
                Notifications.add(response.data && response.data.detail, 'error');
            } else {
                Notifications.add('Unknown error!', 'error');
            }
        })
    }

    $ctrl.cancel = function() {
        $uibModalInstance.dismiss('cancel');
    }
});
