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

angular.module('myApp').controller('ModalInstanceCtrl', function ($uibModalInstance, djangoAuth, data) {
    var $ctrl = this;
    if(data) {
        $ctrl.data = data;
    }
    if(data && data.ip) {
        $ctrl.ip = data.ip;
    }
    if(data && data.field) {
        $ctrl.field = data.field;
    }
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
    $ctrl.updateField = function() {
        $uibModalInstance.close($ctrl.field);
    }
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
    $ctrl.ok = function() {
        $uibModalInstance.close();
    }
    $ctrl.cancel = function () {
        $uibModalInstance.dismiss('cancel');
    };
})
.controller('OverwriteModalInstanceCtrl', function ($uibModalInstance, djangoAuth, data, Profile, SA, TopAlert) {
    var $ctrl = this;
    if(data.file) {
        $ctrl.file = data.file;
    }
    if(data.type) {
        $ctrl.type = data.type;
    }
    if(data.profile) {
        $ctrl.profile = data.profile;
    }
    $ctrl.overwriteProfile = function() {
        return Profile.update($ctrl.profile).$promise.then(function(resource) {
            TopAlert.add("Profile: \"" + resource.name + "\" has been imported" , "success", 5000);
            $ctrl.data = {
                status: "overwritten"
            }
            $uibModalInstance.close($ctrl.data);
            return resource;
        }).catch(function(repsonse) {
            TopAlert.add(response.detail, "error");
        })
    }
    $ctrl.overwriteSa = function() {
        return SA.update($ctrl.profile).$promise.then(function(resource) {
            TopAlert.add("Submission agreement: \"" + resource.name + "\" has been imported" , "success", 5000);
            $ctrl.data = {
                status: "overwritten"
            }
            $uibModalInstance.close($ctrl.data);
            return resource;
        }).catch(function(response) {
            TopAlert.add("Submission Agreement " + $ctrl.profile.name + " is Published and can not be overwritten", "error");
        })
    }
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
.controller('ReceiveModalInstanceCtrl', function (TopAlert, $uibModalInstance, $scope, $rootScope,  djangoAuth, data, Requests, $translate) {
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
    $scope.$on('disable_receive', function () {
        $scope.receiveDisabled = true;
    });
    $scope.$on('update_ip', function (event, data) {
        var temp = angular.copy($scope.ip);
        $scope.ip = data.ip;
        vm.updateCheckedIp({id: temp.id}, $scope.ip);
    });
    $scope.getArchivePolicies().then(function (result) {
        vm.request.archivePolicy.options = result;
        vm.request.archivePolicy.value = $scope.ip.policy;
        vm.request.informationClass = $scope.ip.policy ? $scope.ip.policy.information_class : null;
        $scope.getTags().then(function (result) {
            vm.request.tags.options = result;
            $scope.requestForm = true;
        });
    });
    vm.getProfileData = function ($event) {
        vm.request.submissionAgreement.value = $event.submissionAgreement;
        if ($event.aipProfileId) {
            vm.request.profileData[$event.aipProfileId] = $event.aipModel;
        }
        if($event.dipProfileId) {
            vm.request.profileData[$event.dipProfileId] = $event.dipModel;
        }
        $scope.approvedToReceive = true;
    }
    vm.receive = function (ip) {
        vm.data = {
            status: "received"
        }
        Requests.receive(ip, vm.request, vm.validatorModel)
            .then(function(response){
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
    $ctrl.angular = angular;
    $ctrl.template = data.template;
    if(data.template && data.template.structure) {
        $ctrl.oldStructure = angular.copy(data.template.structure);
    }
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
    $ctrl.saveStructure = function (structure) {
        $ctrl.data = structure;
        ProfileMakerTemplate.update({ templateName: $ctrl.template.name }, { structure: structure })
            .$promise.then(function (resource) {
                $uibModalInstance.close(resource);
            })
    }
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
}).controller('RequestModalInstanceCtrl', function (ProfileMakerTemplate, $uibModalInstance, djangoAuth, data, $scope) {
    var $ctrl = this;
    $ctrl.angular = angular;
    $ctrl.object = data.object;
    $ctrl.requestTypes = data.types;
    $ctrl.request = data.request;
    $ctrl.submit = function() {
        $scope.submitRequest($ctrl.object, $ctrl.request);
        $uibModalInstance.close($ctrl.object);
    }
    $ctrl.cancel = function () {
        $uibModalInstance.dismiss('cancel');
    };
}).controller('AppraisalModalInstanceCtrl', function ($uibModalInstance, djangoAuth, data, $scope, TopAlert) {
    var $ctrl = this;
    $ctrl.angular = angular;
    $ctrl.data = data;
    $ctrl.requestTypes = data.types;
    $ctrl.request = data.request;
    $ctrl.appraisalRules = [
        { id: 'ad961193-6162-4871-9ceb-d464e2276586', name: "Gallring fakturor", frequency: "24h", type: "Arkivobjekt" },
        { id: 'b987a27f-a111-43d6-83cf-dbbab1a8de8c', name: "Gallring lönsespecefikationer", frequency: "1 week", type: "Metadata" },
        { id: '2a4ffd3e-8796-4040-a0ca-7a27420541f9', name: "Rule 4", frequency: "10 years", type: "Metadata" },
        { id: 'fc84bbef-7387-4528-b667-e24efa2940c4', name: "Rule 3", frequency: "24h", type: "Arkivobjekt" },
        { id: 'b53f58f5-b062-4f3d-9c01-31835c90b04c', name: "Rule 6", frequency: "1 year", type: "Metadata" },
        { id: '21fdd706-cbb5-40d5-897a-363939589db6', name: "Rule 5", frequency: "2h", type: "Arkivobjekt" },
        { id: '1bff3bd2-f7df-4555-b539-26c175ac216d', name: "Rule 7", frequency: "Manual", type: "Arkivobjekt" }
    ];
    $ctrl.appraisalRule = null;
    $ctrl.create = function() {
        $ctrl.data = {
            name: $ctrl.name,
            frequency: $ctrl.frequency,
            type: $ctrl.type
        };
        $uibModalInstance.close($ctrl.data);
    }
    $ctrl.ok = function() {
        $uibModalInstance.close();
    }
    $ctrl.cancel = function () {
        $uibModalInstance.dismiss('cancel');
    };
    $ctrl.submitAppraisal = function(appraisal) {
        TopAlert.add($ctrl.data.record.name + ", har lagts till i gallringsregel: " + appraisal.name, "success");
        $uibModalInstance.close(appraisal);
    }
})
