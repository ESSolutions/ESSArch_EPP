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
            TopAlert.add("Profile: \"" + resource.name + "\" has been imported. <br/>ID: " + resource.id , "success", 5000, {isHtml: true});
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
            TopAlert.add("Submission agreement: \"" + resource.name + "\" has been imported. <br/>ID: " + resource.id , "success", 5000, {isHtml: true});
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
}).controller('AppraisalModalInstanceCtrl', function (cronService, $filter, $translate, IP, $uibModalInstance, djangoAuth, appConfig, $http, data, $scope, TopAlert, $timeout) {
    var $ctrl = this;
    // Set later to use local time for next job
    later.date.localTime();
    $ctrl.angular = angular;
    $ctrl.data = data;
    $ctrl.requestTypes = data.types;
    $ctrl.request = data.request;
    $ctrl.appraisalRules = [];
    $ctrl.ip = null;
    $ctrl.showRulesTable = function(ip) {
        $ctrl.ip = ip;
        return $http.get(appConfig.djangoUrl+"appraisal-rules/", {params: {not_related_to_ip: ip.id}}).then(function(response) {
            $ctrl.appraisalRules = response.data;
        }).catch(function(response) {
            TopAlert.add(response.data.detail, "error");
        })
    }
    if(data.preview && data.job) {
        $http.get(appConfig.djangoUrl+"appraisal-jobs/"+data.job.id+"/preview/").then(function(response) {
            $ctrl.jobPreview = response.data;
        })
    }
    $ctrl.expandIp = function(ip) {
        if(ip.expanded) {
            ip.expanded = false;
        } else {
            ip.expanded = true;
            IP.appraisalRules({id: ip.id}).$promise.then(function(resource) {
                ip.rules = resource;
            }).catch(function(response) {
                TopAlert.add(response.data.detail, "error");
            })
        }
    }
    $ctrl.cronConfig = {
        allowMultiple: true
    }
    $ctrl.frequency = "* * * * *";
    $ctrl.myFrequency = null;

    $ctrl.validCron = function(frequency) {
        var months = [
            {name: "jan", days: 31},
            {name: "feb", days: 29},
            {name: "mar", days: 31},
            {name: "apr", days: 30},
            {name: "may", days: 31},
            {name: "jun", days: 30},
            {name: "jul", days: 31},
            {name: "aug", days: 31},
            {name: "sep", days: 30},
            {name: "okt", days: 31},
            {name: "nov", days: 30},
            {name: "dec", days: 31}
        ];
        var cron = cronService.fromCron(frequency, true);
        if(cron.monthValues && cron.dayOfMonthValues) {
            return !cron.monthValues.map(function(month) {
                return !cron.dayOfMonthValues.map(function(day) {
                    return months[month-1].days >= day;
                }).includes(false);
            }).includes(false);
        } else {
            return true;
        }
    }

    $ctrl.prettyFrequency = function(frequency) {
        if($ctrl.validCron(frequency)) {
            return prettyCron.toString(frequency);
        } else {
            return $translate.instant("INVALID_FREQUENCY")
        }
    }
    $ctrl.nextPretty = function(frequency) {
        if($ctrl.validCron(frequency)) {
            return $filter('date')(prettyCron.getNextDate(frequency), "yyyy-MM-dd HH:mm:ss");
        } else {
            return "...";
        }
    }

    $ctrl.addRule = function(ip, rule) {
        $http({
            url: appConfig.djangoUrl+"information-packages/"+ip.id+"/add-appraisal-rule/",
            method: "POST",
            data: {
                id: rule.id
            }
        }).then(function(response) {
            ip.rules.push(rule);
            $ctrl.showRulesTable(ip);
        }).catch(function(response) {
            TopAlert.add(response.data.detail, "error");
        });
    }
    $ctrl.removeRule = function(ip, rule) {
        $http({
            url: appConfig.djangoUrl+"information-packages/"+ip.id+"/remove-appraisal-rule/",
            method: "POST",
            data: {
                id: rule.id
            }
        }).then(function(response) {
            ip.rules.forEach(function(x, index, array) {
                if(x.id == rule.id) {
                    array.splice(index, 1);
                }
            })
            $ctrl.showRulesTable(ip);
        }).catch(function(response) {
            TopAlert.add(response.data.detail, "error");
        });
    }
    $ctrl.closeRulesTable = function(){
        $ctrl.appraisalRules = [];
        $ctrl.ip = null;
    }
    $ctrl.path = "";
    $ctrl.pathList = [];
    $ctrl.addPath = function(path) {
        if(path.length > 0) {
            $ctrl.pathList.push(path);
        }
        $ctrl.path = "";
    }
    $ctrl.removePath = function(path) {
        $ctrl.pathList.splice($ctrl.pathList.indexOf(path), 1);
    }
    $ctrl.appraisalRule = null;
    $ctrl.create = function() {
        if($ctrl.pathList.length == 0) {
            $ctrl.showRequired = true;
            return;
        }
        $ctrl.data = {
            name: $ctrl.name,
            frequency: $ctrl.frequency,
            specification: $ctrl.pathList
        };
        $http({
            url: appConfig.djangoUrl+"appraisal-rules/",
            method: "POST",
            data: $ctrl.data
        }).then(function(response) {
            TopAlert.add("Rule created!", "success")
            $uibModalInstance.close($ctrl.data);
        }).catch(function(response) {
            TopAlert.add(response.data.detail, "error")
        })
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
}).controller('ConversionModalInstanceCtrl', function (cronService, $filter, $translate, IP, $uibModalInstance, djangoAuth, appConfig, $http, data, $scope, TopAlert, $timeout) {
    var $ctrl = this;
    // Set later to use local time for next job
    later.date.localTime();
    $ctrl.angular = angular;
    $ctrl.data = data;
    $ctrl.requestTypes = data.types;
    $ctrl.request = data.request;
    $ctrl.conversionRules = [];
    $ctrl.ip = null;
    $ctrl.showRulesTable = function(ip) {
        $ctrl.ip = ip;
        return $http.get(appConfig.djangoUrl+"conversion-rules/", {params: {not_related_to_ip: ip.id}}).then(function(response) {
            $ctrl.conversionRules = response.data;
        }).catch(function(response) {
            TopAlert.add(response.data.detail, "error");
        })
    }

    $ctrl.expandIp = function(ip) {
        if(ip.expanded) {
            ip.expanded = false;
        } else {
            ip.expanded = true;
            IP.conversionRules({id: ip.id}).$promise.then(function(resource) {
                ip.rules = resource;
            }).catch(function(response) {
                TopAlert.add(response.data.detail, "error");
            })
        }
    }

    $ctrl.cronConfig = {
        allowMultiple: true
    }
    $ctrl.frequency = "* * * * *";
    $ctrl.myFrequency = null;

    $ctrl.validCron = function(frequency) {
        var months = [
            {name: "jan", days: 31},
            {name: "feb", days: 29},
            {name: "mar", days: 31},
            {name: "apr", days: 30},
            {name: "may", days: 31},
            {name: "jun", days: 30},
            {name: "jul", days: 31},
            {name: "aug", days: 31},
            {name: "sep", days: 30},
            {name: "okt", days: 31},
            {name: "nov", days: 30},
            {name: "dec", days: 31}
        ];
        var cron = cronService.fromCron(frequency, true);
        if(cron.monthValues && cron.dayOfMonthValues) {
            return !cron.monthValues.map(function(month) {
                return !cron.dayOfMonthValues.map(function(day) {
                    return months[month-1].days >= day;
                }).includes(false);
            }).includes(false);
        } else {
            return true;
        }
    }

    $ctrl.prettyFrequency = function(frequency) {
        if($ctrl.validCron(frequency)) {
            return prettyCron.toString(frequency);
        } else {
            return $translate.instant("INVALID_FREQUENCY")
        }
    }
    $ctrl.nextPretty = function(frequency) {
        if($ctrl.validCron(frequency)) {
            return $filter('date')(prettyCron.getNextDate(frequency), "yyyy-MM-dd HH:mm:ss");
        } else {
            return "...";
        }
    }

    function getRules() {
        IP.conversionRules({id: ip.id}).$promise.then(function(resource) {
            ip.rules = resource;
        }).catch(function(response) {
            TopAlert.add(response.data.detail, "error");
        })
    }
    if(data.preview && data.job) {
        $http.get(appConfig.djangoUrl+"conversion-jobs/"+data.job.id+"/preview/").then(function(response) {
            $ctrl.jobPreview = response.data;
        })
    }
    $ctrl.addRule = function(ip, rule) {
        $http({
            url: appConfig.djangoUrl+"information-packages/"+ip.id+"/add-conversion-rule/",
            method: "POST",
            data: {
                id: rule.id
            }
        }).then(function(response) {
            ip.rules.push(rule);
            $ctrl.showRulesTable(ip);
        }).catch(function(response) {
            TopAlert.add(response.data.detail, "error");
        });
    }

    $ctrl.specifications = {};
    $ctrl.addSpecification = function() {
        $ctrl.specifications[$ctrl.path] = {
            target: $ctrl.target,
            tool: $ctrl.tool
        }
        $ctrl.path = "";
        $ctrl.target = "";
    }

    $ctrl.deleteSpecification = function(key) {
        delete $ctrl.specifications[key];
    }

    $ctrl.removeRule = function(ip, rule) {
        $http({
            url: appConfig.djangoUrl+"information-packages/"+ip.id+"/remove-conversion-rule/",
            method: "POST",
            data: {
                id: rule.id
            }
        }).then(function(response) {
            ip.rules.forEach(function(x, index, array) {
                if(x.id == rule.id) {
                    array.splice(index, 1);
                }
            })
            $ctrl.showRulesTable(ip);
        }).catch(function(response) {
            TopAlert.add(response.data.detail, "error");
        });
    }
    $ctrl.closeRulesTable = function(){
        $ctrl.conversionRules = [];
        $ctrl.ip = null;
    }
    $ctrl.path = "";
    $ctrl.pathList = [];
    $ctrl.addPath = function(path) {
        if(path.length > 0) {
            $ctrl.pathList.push(path);
        }
    }
    $ctrl.removePath = function(path) {
        $ctrl.pathList.splice($ctrl.pathList.indexOf(path), 1);
    }
    $ctrl.conversionRule = null;
    $ctrl.create = function() {
        if(angular.equals($ctrl.specifications, {})) {
            $ctrl.showRequired = true;
            return;
        }
        $ctrl.data = {
            name: $ctrl.name,
            frequency: $ctrl.frequency,
            specification: $ctrl.specifications
        };
        $http({
            url: appConfig.djangoUrl+"conversion-rules/",
            method: "POST",
            data: $ctrl.data
        }).then(function(response) {
            TopAlert.add("Rule created!", "success")
            $uibModalInstance.close($ctrl.data);
        }).catch(function(response) {
            TopAlert.add(response.data.detail, "error")
        })
    }
    $ctrl.ok = function() {
        $uibModalInstance.close();
    }
    $ctrl.cancel = function () {
        $uibModalInstance.dismiss('cancel');
    };
    $ctrl.submitConversion = function(conversion) {
        TopAlert.add($ctrl.data.record.name + ", har lagts till i konverteringsregerl: " + conversion.name, "success");
        $uibModalInstance.close(conversion);
    }
})
