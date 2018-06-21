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

angular.module('myApp').controller('ModalInstanceCtrl', function ($uibModalInstance, djangoAuth, data, $http, Notifications, IP, appConfig, listViewService) {
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
    $ctrl.newOrder = function(label) {
        $ctrl.creatingOrder = true;
        listViewService.prepareOrder(label).then(function(result) {
            $ctrl.creatingOrder = false;
            $uibModalInstance.close();
        }).catch(function(response) {
            $ctrl.creatingOrder = false;
            Notifications.add(response.data.detail, 'error');
        });
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
    $ctrl.prepare = function (label, objectIdentifierValue, orders) {
        $ctrl.preparing = true;
        listViewService.prepareDip(label, objectIdentifierValue, orders).then(function(response) {
            $ctrl.preparing = false;
            $uibModalInstance.close();
        }).catch(function(response) {
            $ctrl.preparing = false;
            Notifications.add(response.data.detail, 'error');
        })
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
    $ctrl.remove = function (ipObject) {
        $ctrl.removing = true;
        if(data.workarea) {
            if(ipObject.package_type == 1) {
                ipObject.information_packages.forEach(function(ip) {
                    $ctrl.remove(ip, true);
                });
            } else {
                $http.delete(appConfig.djangoUrl + "workarea-entries/" + ipObject.workarea[0].id + "/")
                    .then(function (response) {
                        $ctrl.removing = false;
                        $uibModalInstance.close();
                    }).catch(function (response) {
                        $ctrl.removing = false;
                        if (response.status == 404) {
                            Notifications.add('IP could not be found', 'error');
                        } else {
                            Notifications.add(response.data.detail, 'error');
                        }
                    })
            }
        } else {
            IP.delete({
                id: ipObject.id
            }).$promise.then(function() {
                $ctrl.removing = false;
                $uibModalInstance.close();
            }).catch(function (response) {
                $ctrl.removing = false;
                if (response.status == 404) {
                    Notifications.add('IP could not be found', 'error');
                } else {
                    Notifications.add(response.data.detail, 'error');
                }
            })
        }
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
.controller('OverwriteModalInstanceCtrl', function ($uibModalInstance, djangoAuth, data, Profile, SA, Notifications) {
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
            Notifications.add("Profile: \"" + resource.name + "\" has been imported. <br/>ID: " + resource.id , "success", 5000, {isHtml: true});
            $ctrl.data = {
                status: "overwritten"
            }
            $uibModalInstance.close($ctrl.data);
            return resource;
        }).catch(function(repsonse) {
            Notifications.add(response.detail, "error");
        })
    }
    $ctrl.overwriteSa = function() {
        return SA.update($ctrl.profile).$promise.then(function(resource) {
            Notifications.add("Submission agreement: \"" + resource.name + "\" has been imported. <br/>ID: " + resource.id , "success", 5000, {isHtml: true});
            $ctrl.data = {
                status: "overwritten"
            }
            $uibModalInstance.close($ctrl.data);
            return resource;
        }).catch(function(response) {
            Notifications.add("Submission Agreement " + $ctrl.profile.name + " is Published and can not be overwritten", "error");
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
.controller('ReceiveModalInstanceCtrl', function (Notifications, $uibModalInstance, $scope, $rootScope,  djangoAuth, data, Requests, $translate, IPReception) {
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
        $scope.getArchives().then(function (result) {
            vm.tags.archive.options = result;
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
        if($event.saObject) {
            vm.sa = $event.saObject;
        }
        if($event.approved) {
            $scope.approvedToReceive = $event.approved;
        }
    }
    vm.receive = function (ip) {
        vm.receiving = true;
        IPReception.receive({
                id: ip.id,
                archive_policy: vm.request.archivePolicy.value.id,
                purpose: vm.request.purpose,
                tag: $scope.getDescendantId(),
                allow_unknown_files: vm.request.allowUnknownFiles,
                validators: vm.validatorModel
            }).$promise.then(function(response){
                Notifications.add(response.detail, "success", 3000);
                vm.data = {status: "received"};
                vm.receiving = false;
                $uibModalInstance.close(vm.data);
            }).catch(function(response) {
                vm.receiving = false;
                if(response.status == 404) {
                    Notifications.add('IP could not be found', 'error');
                } else if (response.status != 500 && response.data.detail) {
                    Notifications.add(response.data.detail, 'error');
                }
            })
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
}).controller('AppraisalModalInstanceCtrl', function (cronService, $filter, $translate, IP, $uibModalInstance, djangoAuth, appConfig, $http, data, $scope, Notifications, $timeout) {
    var $ctrl = this;
    // Set later to use local time for next job
    later.date.localTime();
    $ctrl.angular = angular;
    $ctrl.data = data;
    $ctrl.requestTypes = data.types;
    $ctrl.request = data.request;
    $ctrl.appraisalRules = [];
    $ctrl.publicRule = true;
    $ctrl.manualRule = false;
    $ctrl.ip = null;
    $ctrl.showRulesTable = function(ip) {
        $ctrl.ip = ip;
        return $http.get(appConfig.djangoUrl+"appraisal-rules/", {params: {not_related_to_ip: ip.id}}).then(function(response) {
            $ctrl.appraisalRules = response.data;
        }).catch(function(response) {
            Notifications.add(response.data.detail, "error");
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
                Notifications.add(response.data.detail, "error");
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
        $ctrl.addingRule = true;
        $http({
            url: appConfig.djangoUrl+"information-packages/"+ip.id+"/add-appraisal-rule/",
            method: "POST",
            data: {
                id: rule.id
            }
        }).then(function(response) {
            $ctrl.addingRule = false;
            ip.rules.push(rule);
            $ctrl.showRulesTable(ip);
        }).catch(function(response) {
            $ctrl.addingRule = false;
            Notifications.add(response.data.detail, "error");
        });
    }
    $ctrl.removeRule = function(ip, rule) {
        $ctrl.removingRule = true;
        $http({
            url: appConfig.djangoUrl+"information-packages/"+ip.id+"/remove-appraisal-rule/",
            method: "POST",
            data: {
                id: rule.id
            }
        }).then(function(response) {
            $ctrl.removingRule = false;
            ip.rules.forEach(function(x, index, array) {
                if(x.id == rule.id) {
                    array.splice(index, 1);
                }
            })
            $ctrl.showRulesTable(ip);
        }).catch(function(response) {
            $ctrl.removingRule = false;
            Notifications.add(response.data.detail, "error");
        });
    }
    $ctrl.closeRulesTable = function(){
        $ctrl.appraisalRules = [];
        $ctrl.ip = null;
    }

    $ctrl.createJob = function(rule) {
        $ctrl.creatingJob = true;
        $http({
            url: appConfig.djangoUrl + "appraisal-jobs/",
            method: "POST",
            data: {rule: rule.id}
        }).then(function (response) {
            $ctrl.creatingJob = false;
            Notifications.add("Job created!", "success");
            $uibModalInstance.close($ctrl.data);
        }).catch(function (response) {
            $ctrl.creatingJob = false;
            if (response.data.detail) {
                Notifications.add(response.data.detail, "error");
            } else {
                Notifications.add('Unknown error', "error");

            }
        })
    }
    $ctrl.runningJob = false;
    $ctrl.createJobAndStart = function(rule) {
        $ctrl.runningJob = true;
        $http({
            url: appConfig.djangoUrl + "appraisal-jobs/",
            method: "POST",
            data: {rule: rule.id}
        }).then(function (response) {
            $http({
                url: appConfig.djangoUrl + "appraisal-jobs/" + response.data.id + "/run/",
                method: "POST",
            }).then(function (response) {
                $ctrl.runningJob = false;
                Notifications.add("Job running!", "success");
                $uibModalInstance.close($ctrl.data);
            }).catch(function (response) {
                $ctrl.runningJob = false;
                if (response.data.detail) {
                    Notifications.add(response.data.detail, "error");
                } else {
                    Notifications.add('Unknown error', "error");
                }
            })
        }).catch(function (response) {
            $ctrl.addingRule = false;
            if (response.data.detail) {
                Notifications.add(response.data.detail, "error");
            } else {
                Notifications.add('Unknown error', "error");
            }
        })
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
    $ctrl.create = function () {
        $ctrl.addingRule = true;
        if ($ctrl.pathList.length == 0) {
            $ctrl.showRequired = true;
            $ctrl.addingRule = false;
            return;
        }
        $ctrl.data = {
            name: $ctrl.name,
            frequency: $ctrl.manualRule ? '' : $ctrl.frequency,
            specification: $ctrl.pathList,
            public: $ctrl.publicRule
        };
        $http({
            url: appConfig.djangoUrl + "appraisal-rules/",
            method: "POST",
            data: $ctrl.data
        }).then(function (response) {
            $ctrl.addingRule = false;
            Notifications.add("Rule created!", "success");
            $uibModalInstance.close($ctrl.data);
        }).catch(function (response) {
            $ctrl.addingRule = false;
            if (response.data.detail) {
                Notifications.add(response.data.detail, "error");
            } else {
                Notifications.add('Unknown error', "error");

            }
        })
    }

    $ctrl.removeAppraisal = function() {
        $ctrl.removingRule = true;
        var appraisal = data.appraisal;
        $http({
            url: appConfig.djangoUrl+"appraisal-rules/"+appraisal.id,
            method: "DELETE"
        }).then(function(response) {
            $ctrl.removingRule = false;
            Notifications.add("Appraisal rule: "+appraisal.name+" has been removed", "success");
            $uibModalInstance.close();
        }).catch(function(response) {
            $ctrl.removingRule = false;
            Notifications.add("Appraisal rule could not be removed", "error");
        })
    }

    $ctrl.ok = function() {
        $uibModalInstance.close();
    }
    $ctrl.cancel = function () {
        $uibModalInstance.dismiss('cancel');
    };
    $ctrl.submitAppraisal = function(appraisal) {
        Notifications.add($ctrl.data.record.name + ", har lagts till i gallringsregel: " + appraisal.name, "success");
        $uibModalInstance.close(appraisal);
    }
}).controller('ConversionModalInstanceCtrl', function (cronService, $filter, $translate, IP, $uibModalInstance, djangoAuth, appConfig, $http, data, $scope, Notifications, $timeout) {
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
            Notifications.add(response.data.detail, "error");
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
                Notifications.add(response.data.detail, "error");
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
            Notifications.add(response.data.detail, "error");
        })
    }
    if(data.preview && data.job) {
        $http.get(appConfig.djangoUrl+"conversion-jobs/"+data.job.id+"/preview/").then(function(response) {
            $ctrl.jobPreview = response.data;
        })
    }
    $ctrl.addRule = function(ip, rule) {
        $ctrl.addingRule = true;
        $http({
            url: appConfig.djangoUrl+"information-packages/"+ip.id+"/add-conversion-rule/",
            method: "POST",
            data: {
                id: rule.id
            }
        }).then(function(response) {
            $ctrl.addingRule = false;
            ip.rules.push(rule);
            $ctrl.showRulesTable(ip);
        }).catch(function(response) {
            $ctrl.addingRule = false;
            Notifications.add(response.data.detail, "error");
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
        $ctrl.removingRule = true;
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
            $ctrl.removingRule = false;
            $ctrl.showRulesTable(ip);
        }).catch(function(response) {
            $ctrl.removingRule = false;
            Notifications.add(response.data.detail, "error");
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
        $ctrl.addingRule = true;
        if(angular.equals($ctrl.specifications, {})) {
            $ctrl.showRequired = true;
            $ctrl.addingRule = false;
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
            $ctrl.addingRule = false;
            Notifications.add("Rule created!", "success")
            $uibModalInstance.close($ctrl.data);
        }).catch(function(response) {
            $ctrl.addingRule = false;
            Notifications.add(response.data.detail, "error")
        })
    }

    $ctrl.removeConversion = function() {
        $ctrl.removingRule = true;
        var conversion = data.conversion;
        $http({
            url: appConfig.djangoUrl+"conversion-rules/"+conversion.id,
            method: "DELETE"
        }).then(function(response) {
            $ctrl.removingRule = false;
            Notifications.add("conversion rule: "+conversion.name+" has been removed", "success");
            $uibModalInstance.close();
        }).catch(function(response) {
            $ctrl.removingRule = false;
            Notifications.add("conversion rule could not be removed", "errorepp");
        })
    }

    $ctrl.ok = function() {
        $uibModalInstance.close();
    }
    $ctrl.cancel = function () {
        $uibModalInstance.dismiss('cancel');
    };
    $ctrl.submitConversion = function(conversion) {
        Notifications.add($ctrl.data.record.name + ", har lagts till i konverteringsregerl: " + conversion.name, "success");
        $uibModalInstance.close(conversion);
    }
}).controller('EditNodeModalInstanceCtrl', function (Search, $translate, $uibModalInstance, djangoAuth, appConfig, $http, data, $scope, Notifications, $timeout, $q) {
    var $ctrl = this;
    $ctrl.node = data.node;
    $ctrl.editData = {};
    $ctrl.editFields = [];
    $ctrl.editFieldsNoDelete = [];
    $ctrl.options = {};
    $ctrl.fieldOptions = {};
    $ctrl.newFieldKey = null;
    $ctrl.newFieldVal = null;
    $ctrl.updateDescendants = false;
    $ctrl.manyNodes = false;
    $ctrl.$onInit = function() {
        if(angular.isArray(data.node)) {
            $ctrl.nodeList = data.node.map(function(x) {
                return x._id;
            }).join(',');
            $ctrl.nameList = data.node.map(function(x) {
                return x._source.name;
            }).join(', ');
            $ctrl.node = data.node[0];
            $ctrl.node._source = data.node.reduce(function(result, currentObject) {
                for(var key in currentObject._source) {
                    if (currentObject._source.hasOwnProperty(key)) {
                        result[key] = currentObject._source[key];
                    }
                }
                return result;
            }, {});
            $ctrl.manyNodes = true;
        }
        $ctrl.arrayFields = [];
        $ctrl.fieldOptions = getEditableFields($ctrl.node);
        var discludedFields = ["archive", "current_version"];
        angular.forEach($ctrl.fieldOptions, function(value, field) {
            if(!discludedFields.includes(field)) {
                if(angular.isArray(value)) {
                    $ctrl.arrayFields.push(field);
                    addStandardField(field, value.join(','));
                } else {
                    switch(typeof(value)) {
                        case "object":
                        clearObject($ctrl.node._source[field]);
                        addNestedField(field, value)
                        break;
                        default:
                        addStandardField(field, value);
                        break;
                    }
                }
            }
        })
    }

    $ctrl.noDeleteFields = {
        component: ['name'],
        document: ['name'],
        archive: ['name'],
        information_package: ['name']
    }

    $ctrl.fieldsToDelete = [];
    function deleteField(field) {
        var splitted = field.split('.');
        if (!angular.isUndefined($ctrl.node._source[field]) || (splitted.length > 1 && !angular.isUndefined($ctrl.node._source[splitted[0]][splitted[1]]))) {
            $ctrl.fieldsToDelete.push(field);
        }
        $ctrl.editFields.forEach(function(item, idx, list) {
            if(splitted.length > 1) {
                if(item.templateOptions.label === field) {
                    list.splice(idx, 1);
                }
            } else {
                if(item.key === field) {
                    list.splice(idx, 1);
                }
            }
        })
        if(splitted.length > 1) {
            delete $ctrl.editData[splitted[0]][splitted[1]];
        } else {
            delete $ctrl.editData[field];
        }
    }

    function addNestedField(field, value) {
        var model = {};
        var group = {
            "templateOptions": {
                "label":field,
            },
            "fieldGroup": []
        };
        angular.forEach(value, function (val, key) {
            model[key] = val;
            if ($ctrl.noDeleteFields[$ctrl.node._index].includes(field + '.' + key)) {
                $ctrl.editFieldsNoDelete.push(
                    {
                        "templateOptions": {
                            "type": "text",
                            "label": field + '.' + key,
                        },
                        "type": "input",
                        "model": 'model.' + field,
                        "key": key,
                    }
                )
            } else {
                $ctrl.editFields.push(
                    {
                        "templateOptions": {
                            "type": "text",
                            "label": field + '.' + key,
                            "delete": function () { deleteField(field + '.' + key) }
                        },
                        "type": "input",
                        "model": 'model.' + field,
                        "key": key,
                    }
                )
            }
        })
        if(!$ctrl.manyNodes) {
            $ctrl.editData[field] = model;
        } else {
            $ctrl.editData[field] = model;
        }
    }

    function clearObject(obj) {
        angular.forEach(obj, function(val, key) {
            obj[key] = null;
        })
    }

    function addStandardField(field, value) {
        if(!$ctrl.manyNodes) {
            $ctrl.editData[field] = value;
        } else {
            $ctrl.editData[field] = null;
        }
        if ($ctrl.noDeleteFields[$ctrl.node._index].includes(field)) {
            $ctrl.editFieldsNoDelete.push(
                {
                    "templateOptions": {
                        "type": "text",
                        "label": field,
                    },
                    "type": "input",
                    "key": field,
                }
            )
        } else {

            $ctrl.editFields.push(
                {
                    "templateOptions": {
                        "type": "text",
                        "label": field,
                        "delete": function () { deleteField(field) }
                    },
                    "type": "input",
                    "key": field,
                }
            )
        }
    }

    function getEditableFields(node) {
        return node._source;
    }
    $ctrl.selected = null;

    $ctrl.changed = function() {
        return !angular.equals(getEditedFields($ctrl.editData), {});
    }

    $ctrl.addNewField = function () {
        if ($ctrl.newFieldKey && $ctrl.newFieldVal) {
            var newFieldKey = angular.copy($ctrl.newFieldKey);
            var newFieldVal = angular.copy($ctrl.newFieldVal);
            var splitted = newFieldKey.split('.');
            if((splitted.length > 1 && !angular.isUndefined($ctrl.editData[splitted[0]][splitted[1]]))|| !angular.isUndefined($ctrl.editData[newFieldKey])) {
                Notifications.add($translate.instant('FIELD_EXISTS'), 'error')
                return;
            }
            if(splitted.length > 1) {
                $ctrl.editData[splitted[0]][splitted[1]] = newFieldVal;
            } else {
                $ctrl.editData[newFieldKey] = newFieldVal;
            }
            $ctrl.editFields.push(
                {
                    "templateOptions": {
                        "type": "text",
                        "label": newFieldKey,
                        "delete": function () { deleteField(newFieldKey) }
                    },
                    "type": "input",
                    "key": newFieldKey,
                }
            )
            if ($ctrl.fieldsToDelete.includes(newFieldKey)) {
                $ctrl.fieldsToDelete.splice($ctrl.fieldsToDelete.indexOf(newFieldKey), 1);
            }
            $ctrl.newFieldKey = null;
            $ctrl.newFieldVal = null;
        }
    }

    function getEditedFields(data) {
        var edited = {};
        angular.forEach(data, function(value, key) {
            if(typeof(value) === 'object' && !angular.isArray(value)) {
                angular.forEach(value, function(val, k) {
                    if($ctrl.node._source[key][k] !== val) {
                        if(!edited[key]) {
                            edited[key] = {};
                        }
                        edited[key][k] = val;
                    }
                })
            } else {
                if($ctrl.node._source[key] != value) {
                    edited[key] = value;
                }
            }
        })
        return edited;
    }

    $ctrl.editField = function(field, value) {
        $ctrl.editData[field] = value;
        $ctrl.editFields.push(
            {
                "templateOptions": {
                    "type": "text",
                    "label": field,
                },
                "type": "input",
                "key": field,
            }
        )
    }

    $ctrl.updateSingleNode = function() {
        if ($ctrl.changed() || $ctrl.fieldsToDelete.length > 0) {
            $ctrl.submitting = true;
            var promises = [];
            $ctrl.fieldsToDelete.forEach(function (item) {
                promises.push(
                    $http.post(appConfig.djangoUrl + 'search/' + $ctrl.node._index + '/' + $ctrl.node._id + '/delete-field/', { field: item })
                        .then(function (response) {
                            return response;
                        }).catch(function (response) {
                            $ctrl.submitting = false;
                            if (response.data.detail) {
                                Notifications.add(response.data.detail, 'error');
                            } else {
                                Notifications.add('Unknown error', 'error');
                            }
                            return response;
                        })
                );
            });
            $q.all(promises).then(function (results) {
                if($ctrl.changed()) {
                    Search.updateNode($ctrl.node, getEditedFields($ctrl.editData)).then(function (response) {
                        $ctrl.submitting = false;
                        Notifications.add($translate.instant('NODE_EDITED'), 'success');
                        $uibModalInstance.close("edited");
                    }).catch(function (response) {
                        $ctrl.submitting = false;
                        Notifications.add(response.data, 'error');
                    });
                } else {
                    $ctrl.submitting = false;
                    Notifications.add($translate.instant('NODE_EDITED'), 'success');
                    $uibModalInstance.close("edited");
                }
            }).catch(function (response) {
                $ctrl.submitting = false;
                if (response.data.detail) {
                    Notifications.add(response.data.detail, 'error');
                } else {
                    Notifications.add('Unknown error', 'error');
                }
            });
        }
    }

    $ctrl.updateNodeAndDescendants = function() {
        if ($ctrl.changed() || $ctrl.fieldsToDelete.length > 0) {
            Search.updateNodeAndDescendants($ctrl.node, getEditedFields($ctrl.editData), $ctrl.fieldsToDelete.join(',')).then(function (response) {
                $ctrl.submitting = false;
                Notifications.add($translate.instant('NODE_EDITED'), 'success');
                $uibModalInstance.close("edited");
            }).catch(function (response) {
                $ctrl.submitting = false;
                Notifications.add('Could not update nodes', 'error');
            });
        }
    }

    $ctrl.massUpdate = function() {
        if ($ctrl.changed() || $ctrl.fieldsToDelete.length > 0) {
            Search.massUpdate($ctrl.nodeList, getEditedFields($ctrl.editData), $ctrl.fieldsToDelete.join(',')).then(function (response) {
                $ctrl.submitting = false;
                Notifications.add($translate.instant('NODE_EDITED'), 'success');
                $uibModalInstance.close("edited");
            }).catch(function (response) {
                $ctrl.submitting = false;
                Notifications.add('Could not update nodes', 'error');
            });
        }
    }

    $ctrl.submit = function () {
        convertArrayFields();
        if($ctrl.manyNodes) {
            $ctrl.massUpdate();
        } else if($ctrl.updateDescendants) {
            $ctrl.updateNodeAndDescendants();
        } else {
            $ctrl.updateSingleNode();
        }
    }

    function convertArrayFields() {
        $ctrl.arrayFields.forEach(function(field) {
            if(!$ctrl.fieldsToDelete.includes(field) && $ctrl.editData[field] != $ctrl.node._source[field]) {
                $ctrl.editData[field] = $ctrl.editData[field].split(',');
            }
        })
    }

    $ctrl.cancel = function() {
        $uibModalInstance.dismiss('cancel');
    }
}).controller('AddNodeModalInstanceCtrl', function (Search, $translate, $uibModalInstance, djangoAuth, appConfig, $http, data, $scope, Notifications, $timeout) {
    var $ctrl = this;
    $ctrl.node = data.node.original;
    $ctrl.newNode = {
        reference_code: data.node.children.length+1,
    };
    $ctrl.options = {};
    $ctrl.nodeFields = [];
    $ctrl.indexes = [];
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
                    "label": $translate.instant("INDEX"),
                    "options": $ctrl.indexes,
                    "required": true,
                    "labelProp": "name",
                    "valueProp": "name"
                },
                "type": "select",
                "key": "index",
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
                Notifications.add(response.data.detail, 'error');
            })
        }
    }
    $ctrl.cancel = function() {
        $uibModalInstance.dismiss('cancel');
    }
})
.controller('VersionModalInstanceCtrl', function (Search, $translate, $uibModalInstance, djangoAuth, appConfig, $http, data, $scope, Notifications, $timeout) {
    var $ctrl = this;
    $ctrl.node = data.node.original;

    $ctrl.$onInit = function () {}

    $ctrl.createNewVersion = function(node) {
        Search.createNewVersion(node).then(function(response) {
            Notifications.add($translate.instant('NEW_VERSION_CREATED'), 'success');
            $uibModalInstance.close("added");
        }).catch(function(response) {
            Notifications.add(response.data.detail, 'error');
        })
    }
    $ctrl.cancel = function() {
        $uibModalInstance.dismiss('cancel');
    }
})
.controller('RemoveNodeModalInstanceCtrl', function (Search, $translate, $uibModalInstance, djangoAuth, appConfig, $http, data, $scope, Notifications, $timeout) {
    var $ctrl = this;
    $ctrl.data = data;
    $ctrl.node = data.node.original;

    $ctrl.$onInit = function () {}

    $ctrl.remove = function() {
        Search.removeNode($ctrl.node).then(function(response) {
            Notifications.add($translate.instant('NODE_REMOVED'), 'success');
            $uibModalInstance.close("added");
        }).catch(function(response) {
            Notifications.add(response.data.detail, 'error');
        })
    }
    $ctrl.removeFromStructure = function() {
        Search.removeNodeFromStructure($ctrl.node, $ctrl.data.structure.id).then(function(response) {
            Notifications.add($translate.instant('NODE_REMOVED_FROM_STRUCTURE'), 'success');
            $uibModalInstance.close("removed");
        }).catch(function(response) {
            Notifications.add(response.data.detail, 'error');
        })
    }
    $ctrl.cancel = function() {
        $uibModalInstance.dismiss('cancel');
    }
})
.controller('StructureModalInstanceCtrl', function (Search, $translate, $uibModalInstance, djangoAuth, appConfig, $http, data, $scope, Notifications, $timeout) {
    var $ctrl = this;
    $ctrl.node = data.node;
    $ctrl.creating = false;
    $ctrl.$onInit = function () {}

    $ctrl.createNewStructure = function(node) {
        $ctrl.creating = true;
        Search.createNewStructure(node, { name: $ctrl.structureName }).then(function (response) {
            Notifications.add($translate.instant('NEW_STRUCTURE_CREATED'), 'success');
            $uibModalInstance.close("added");
            $ctrl.creating = false;
        }).catch(function (response) {
            $ctrl.creating = false;
            Notifications.add('Error creating new structure', 'error');
        })
    }
    $ctrl.cancel = function() {
        $uibModalInstance.dismiss('cancel');
    }
});
