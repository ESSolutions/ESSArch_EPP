angular.module('essarch.controllers').controller('AppraisalModalInstanceCtrl', function (cronService, $filter, $translate, IP, $uibModalInstance, djangoAuth, appConfig, $http, data, $scope, Notifications, $timeout) {
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
});
