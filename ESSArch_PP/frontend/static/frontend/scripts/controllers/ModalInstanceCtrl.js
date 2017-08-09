/*
    ESSArch is an open source archiving and digital preservation system

    ESSArch Preservation Platform (EPP)
    Copyright (C) 2005-2017 ES Solutions AB

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program. If not, see <http://www.gnu.org/licenses/>.

    Contact information:
    Web - http://www.essolutions.se
    Email - essarch@essolutions.se
*/

angular.module('myApp').controller('ModalInstanceCtrl', function ($uibModalInstance, djangoAuth) {
    var $ctrl = this;
    $ctrl.editMode = false;
    $ctrl.error_messages_old = [];
    $ctrl.error_messages_pw1 = [];
    $ctrl.error_messages_pw2 = [];
    $ctrl.tracebackCopied = false;
    $ctrl.copied = function() {
        $ctrl.tracebackCopied = true;
    }
    $ctrl.idCopied = false;
    $ctrl.idCopyDone = function() {
        $ctrl.idCopied = true;
    }
    $ctrl.objectIdentifierValue = "";
    $ctrl.orders = [];
    $ctrl.label = "";
    $ctrl.dir_name = "";
    $ctrl.email = {
        subject: "",
        body: ""
    };
    $ctrl.newOrder = function() {
        $ctrl.data = {
            label: $ctrl.label
        }
        $uibModalInstance.close($ctrl.data);
    };
    $ctrl.save = function () {
        $ctrl.data = {
            name: $ctrl.profileName
        };
        $uibModalInstance.close($ctrl.data);
    };
    $ctrl.saveDir = function () {
        $ctrl.data = {
            dir_name: $ctrl.dir_name
        };
        $uibModalInstance.close($ctrl.data);
    };
    $ctrl.saveTag = function() {
        $ctrl.data = {
            name: $ctrl.name,
            desc: $ctrl.desc
        }
        $uibModalInstance.close($ctrl.data);
    }
    $ctrl.prepare = function () {
        $ctrl.data = {
            label: $ctrl.label,
            objectIdentifierValue: $ctrl.objectIdentifierValue,
            orders: $ctrl.orders
        };
        $uibModalInstance.close($ctrl.data);
    };
    $ctrl.addTag = function () {
        $ctrl.data = {
            name: $ctrl.name,
            desc: $ctrl.desc
        };
        $uibModalInstance.close($ctrl.data);
    };
    $ctrl.lock = function () {
        $ctrl.data = {
            status: "locked"
        }
        $uibModalInstance.close($ctrl.data);
    };
    $ctrl.lockSa = function() {
        $ctrl.data = {
            status: "locked"
        }
        $uibModalInstance.close($ctrl.data);
    };
    $ctrl.remove = function () {
        $ctrl.data = {
            status: "removed"
        }
        $uibModalInstance.close($ctrl.data);
    };
    $ctrl.submit = function () {
        $ctrl.data = {
            email: $ctrl.email,
            status: "submitting"
        }
        $uibModalInstance.close($ctrl.data);
    };
    $ctrl.overwrite = function () {
        $ctrl.data = {
            status: "overwritten"
        }
        $uibModalInstance.close($ctrl.data);
    };
    $ctrl.changePassword = function () {
        djangoAuth.changePassword($ctrl.pw1, $ctrl.pw2, $ctrl.oldPw).then(function(response) {
            $uibModalInstance.close($ctrl.data);
        }, function(error) {
            $ctrl.error_messages_old = error.old_password || [];
            $ctrl.error_messages_pw1 = error.new_password1 || [];
            $ctrl.error_messages_pw2 = error.new_password2 || [];
        });
    };
    $ctrl.cancel = function () {
        $uibModalInstance.dismiss('cancel');
    };
})
.controller('OverwriteModalInstanceCtrl', function ($uibModalInstance, djangoAuth, data) {
    var $ctrl = this;
    $ctrl.file = data.file;
    $ctrl.type = data.type;
    $ctrl.overwrite = function () {
        $ctrl.data = {
            status: "overwritten"
        }
        $uibModalInstance.close($ctrl.data);
    };
    $ctrl.cancel = function () {
        $uibModalInstance.dismiss('cancel');
    };
})
.controller('ReceiveModalInstanceCtrl', function ($uibModalInstance, $scope, $rootScope,  djangoAuth, data, Requests, $translate) {
    var vm = data.vm;
    $scope.saAlert = null;
    $scope.alerts = {
        receiveError: { type: 'danger', msg: $translate.instant('CANNOT_RECEIVE_ERROR') },
    };
    $scope.ip = data.ip;
    $scope.requestForm = true;
    $scope.approvedToReceive = false;
    $scope.profileEditor = true;
    $scope.receiveDisabled = false;

    $scope.$on('disable_receive', function() {
        $scope.receiveDisabled = true;
    });

    vm.getProfileData = function($event) {
        vm.request.submissionAgreement.value = $event.submissionAgreement;
        vm.request.profileData[$event.profileId] = $event.model;
        $scope.approvedToReceive = true;
    }
    vm.receive = function (ip) {
        vm.data = {
            status: "received"
        }
        Requests.receive(ip, vm.request, vm.validatorModel)
            .then(function(){
                $uibModalInstance.close(vm.data);
            });
    };
    vm.fetchProfileData = function() {
        if($scope.approvedToReceive) {
            $scope.approvedToReceive = false;
            $scope.$broadcast('get_profile_data', {})
        }
    }
    vm.skip = function() {
        vm.data = {
            status: "skip"
        }
        $uibModalInstance.close(vm.data);     
    }
    vm.cancel = function () {
        $uibModalInstance.dismiss('cancel');
    };
}).controller('TemplateModalInstanceCtrl', function (ProfileMakerTemplate, $uibModalInstance, djangoAuth, data) {
    var $ctrl = this;
    $ctrl.template = data.template;
    $ctrl.allAttributes = data.allAttributes;
    $ctrl.save = data.save;
    $ctrl.model = data.model;
    $ctrl.fields = data.fields;
    $ctrl.treeOptions = {
        nodeChildren: "children",
        dirSelectable: true,
        injectClasses: {
            ul: "a1",
            li: "a2",
            liSelected: "a7",
            iExpanded: "a3",
            iCollapsed: "a4",
            iLeaf: "a5",
            label: "a6",
            labelSelected: "a8"
        }
    };
    $ctrl.generateTemplate = function () {
        $ctrl.data = $ctrl.model;
        data.generate($ctrl.data).then(function(response) {
            $uibModalInstance.close(response);
        })
    };
    $ctrl.addTemplate = function () {
        $ctrl.data = $ctrl.model;
        data.add($ctrl.data).then(function(response) {
            $uibModalInstance.close(response);
        })
    };
    $ctrl.addExtension = function () {
        $ctrl.data = $ctrl.model;
        data.add($ctrl.data).then(function (data) {
            $ctrl.template.extensions.push(data.id);
            ProfileMakerTemplate.update(
                { templateName: $ctrl.template.name },
                {
                    extensions: $ctrl.template.extensions,
                }).$promise.then(function (resource) {
                    $uibModalInstance.close(resource);
                })
        })
    };
    $ctrl.saveAttribute = function () {
        $ctrl.data = $ctrl.model;
        data.save($ctrl.data).then(function(response) {
            $uibModalInstance.close(response);
        })
    };
    $ctrl.addAttribute = function (nodeData, parent) {
        data.add(nodeData, parent).then(function(response) {
            $uibModalInstance.close(response);
        });
    };
    $ctrl.cancel = function () {
        $uibModalInstance.dismiss('cancel');
    };
})