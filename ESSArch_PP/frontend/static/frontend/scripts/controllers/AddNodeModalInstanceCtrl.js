angular.module('essarch.controllers').controller('AddNodeModalInstanceCtrl', function (Search, $translate, $uibModalInstance, djangoAuth, appConfig, $http, data, $scope, Notifications, $timeout) {
    var $ctrl = this;
    $ctrl.node = data.node.original;
    $ctrl.newNode = {
        reference_code: data.node.children.length+1,
        index: 'component'
    };
    $ctrl.options = {};
    $ctrl.nodeFields = [];
    $ctrl.types = [];

    $ctrl.$onInit = function () {
        $ctrl.indexes = [
            {
                name: "component",
            }
        ];

        $ctrl.nodeFields = [
            {
                "templateOptions": {
                    "type": "text",
                    "label": $translate.instant("NAME"),
                    "required": true,
                    "focus": true
                },
                "type": "input",
                "key": "name",
            },
            {
                "templateOptions": {
                    "label": $translate.instant("TYPE"),
                    "type": "text",
                    "required": true
                },
                "type": "input",
                "key": "type",
            },
            {
                "templateOptions": {
                    "label": $translate.instant("REFERENCE_CODE"),
                    "type": "text",
                    "required": true
                },
                "type": "input",
                "key": "reference_code",
            },
        ];
    }

    $ctrl.changed = function() {
        return !angular.equals($ctrl.newNode, {});
    }

    $ctrl.submit = function() {
        if($ctrl.changed()) {
            $ctrl.submitting = true;
            Search.addNode(angular.extend($ctrl.newNode, {parent: $ctrl.node._id, parent_index: $ctrl.node._index, structure: data.structure})).then(function(response) {
                $ctrl.submitting = false;
                Notifications.add($translate.instant('NODE_ADDED'), 'success');
                $uibModalInstance.close(response.data);
            }).catch(function(response) {
                $ctrl.submitting = false;
                if(![401, 403, 500, 503].includes(response.status)) {
                    if(response.data && response.data.detail) {
                        Notifications.add(response.data.detail, "error");
                    } else {
                        Notifications.add($translate('UNKNOWN_ERROR'), 'error')
                    }
                }
            })
        }
    }
    $ctrl.cancel = function() {
        $uibModalInstance.dismiss('cancel');
    }
});
