angular.module('myApp').controller('ClassificationModalInstanceCtrl', function(data, $http, appConfig, Notifications, $uibModalInstance, $translate, Structure) {
    var $ctrl = this;
    $ctrl.name = null;
    $ctrl.newNode = {};
    $ctrl.options = {};
    $ctrl.nodeFields = [];
    $ctrl.types = [];
    $ctrl.$onInit = function() {
        if(data.node) {
            $ctrl.node = data.node;
        }
        if(data.structure) {
            $ctrl.structure = data.structure;
        };

        $ctrl.nodeFields = [
            {
                "templateOptions": {
                    "label": $translate.instant("REFERENCE_CODE"),
                    "type": "text",
                    "required": true,
                    "focus": true
                },
                "type": "input",
                "key": "reference_code",
            },
            {
                "templateOptions": {
                    "type": "text",
                    "label": $translate.instant("NAME"),
                    "required": true,
                },
                "type": "input",
                "key": "name",
            },
            {
                "templateOptions": {
                    "label": $translate.instant("TYPE"),
                    "type": "text",
                    "options": [
                        {
                            name: "Verksamhetsområde",
                            value: "Verksamhetsområde"
                        },
                        {
                            name: "Processgrupp",
                            value: "Processgrupp"
                        },
                        {
                            name: "Process",
                            value: "Process"
                        }
                    ],
                    "required": true
                },
                "defaultValue": "Verksamhetsområde",
                "type": "select",
                "key": "type",
            },
            {
                "templateOptions": {
                    "label": $translate.instant("DESCRIPTION"),
                    "type": "text",
                    "rows": 3
                },
                "type": "textarea",
                "key": "description",
            },
        ];
    }

    $ctrl.changed = function() {
        return !angular.equals($ctrl.newNode, {});
    }

    $ctrl.remove = function() {
        $http.delete(appConfig.djangoUrl + 'classification-structures/' + data.structure.id + '/units/' + $ctrl.node.id).then(function(response) {
            Notifications.add($translate.instant('NODE_REMOVED'), 'success');
            $uibModalInstance.close("added");
        }).catch(function(response) {
            Notifications.add(response.data.detail, 'error');
        })
    }

    $ctrl.submit = function () {
        if ($ctrl.changed()) {
            $ctrl.submitting = true;
            $http.post(appConfig.djangoUrl + 'classification-structures/' + data.structure.id + '/units/',
                angular.extend(
                    $ctrl.newNode,
                    {
                        parent: $ctrl.node.id,
                    })).then(function (response) {
                        $ctrl.submitting = false;
                        Notifications.add($translate.instant('NODE_ADDED'), 'success');
                        $uibModalInstance.close(response.data);
                    }).catch(function (response) {
                        $ctrl.submitting = false;
                        Notifications.add(response.data.detail, 'error');
                    })
        }
    }
    /**
     * update new classification structure
     */
    $ctrl.update = function() {
        $http({
            method: 'PATCH',
            url: appConfig.djangoUrl + 'classification-structures/' + data.structure.id + '/units/' + $ctrl.node.id + '/',
            data: {
                name: $ctrl.name
            }
        }).then(function(response) {
            $uibModalInstance.close(response.data);
            Notifications.add($translate.instant('NODE_UPDATED'), 'success');
        }).catch(function(response) {
            if(response.data && response.data.detail) {
                Notifications.add(response.data && response.data.detail, 'error');
            } else {
                Notifications.add('Unknown error!', 'error');
            }
        })
    }
    /**
     * Save new classification structure
     */
    $ctrl.save = function() {
        Structure.new(
            {
                name: $ctrl.name
            }
        ).$promise.then(function(response) {
            $uibModalInstance.close(response.data);
            Notifications.add($translate.instant('CLASSIFICATION_STRUCTURE_CREATED'), 'success');
        }).catch(function(response) {
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
})
