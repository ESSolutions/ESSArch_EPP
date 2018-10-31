angular.module('essarch.controllers').controller('ConversionModalInstanceCtrl', function (cronService, $filter, $translate, IP, $uibModalInstance, djangoAuth, appConfig, $http, data, $scope, Notifications, $timeout, ErrorResponse) {
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
            ErrorResponse.default(response);
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
                ErrorResponse.default(response);
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
            ErrorResponse.default(response);
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
            ErrorResponse.default(response);
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
            ErrorResponse.default(response);
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
            specification: $ctrl.specifications,
            description: $ctrl.description
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
            ErrorResponse.default(response);
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
            ErrorResponse.default(response);
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
});
