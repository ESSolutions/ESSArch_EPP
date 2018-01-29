angular.module('myApp').controller('ConversionCtrl', function(ArchivePolicy, $scope, $controller, $rootScope, $cookies, $stateParams, appConfig, $http, $timeout, $uibModal, $log, $sce, $window, TopAlert, $filter, $interval) {
    var vm = this;
    vm.rulesPerPage = 10;
    vm.ongoingPerPage = 10;
    vm.nextPerPage = 10;
    vm.finishedPerPage = 10;
    $scope.ruleLoading = false;
    $scope.ongoingLoading = false;
    $scope.nextLoading = false;
    $scope.finishedLoading = false;

        //Cancel update intervals on state change
        $scope.$on('$stateChangeStart', function() {
            $interval.cancel(conversionInterval);
        });
    var conversionInterval = $interval(function() {
        vm.rulePipe(vm.ruleTableState);
        vm.nextPipe(vm.nextTableState);
        vm.ongoingPipe(vm.ongoingTableState);
        vm.finishedPipe(vm.finishedTableState);
    }, appConfig.ipInterval);

    $scope.$on('REFRESH_LIST_VIEW', function (event, data) {
        vm.rulePipe(vm.ruleTableState);
        vm.nextPipe(vm.nextTableState);
        vm.ongoingPipe(vm.ongoingTableState);
        vm.finishedPipe(vm.finishedTableState);
    });

    /**
     * Smart table pipe function for conversion rules
     * @param {*} tableState
     */
    vm.rulePipe = function(tableState) {
        if(tableState && tableState.search.predicateObject) {
            var search = tableState.search.predicateObject["$"];
        }
        $scope.ruleLoading = true;
        $http.get(appConfig.djangoUrl+"conversion-rules/", {params: {search: search}}).then(function(response) {
            vm.ruleTableState = tableState;
            vm.ruleFilters.forEach(function(x) {
                response.data.forEach(function(rule) {
                    if(x == rule.id) {
                        rule.usedAsFilter = true;
                    }
                });
            });
            vm.rules = response.data;
            $scope.ruleLoading = false;
        }).catch(function(response) {
            TopAlert.add("Failed to get conversion rules", "error");
            $scope.ruleLoading = false;
        })
    }

    /**
     * Smart table pipe function for ongoing conversions
     * @param {*} tableState
     */
    vm.ongoingPipe = function(tableState) {
        $scope.ongoingLoading = true;
        $http.get(appConfig.djangoUrl+"conversion-jobs/", {params: {status: "STARTED"}}).then(function(response) {
            vm.ongoingTableState = tableState;
            vm.ongoing = response.data;
            $scope.ongoingLoading = false;

        }).catch(function(response) {
            TopAlert.add("Failed to get ongoing conversion jobs", "error");
            $scope.ongoingLoading = false;
        })
    }

    /**
     * Smart table pipe function for next conversions
     * @param {*} tableState
     */
    vm.nextPipe = function(tableState) {
        $scope.nextLoading = true;
        $http.get(appConfig.djangoUrl+"conversion-jobs/", { params: {status: "PENDING"}}).then(function(response) {
            vm.nextTableState = tableState;
            vm.next = response.data;
            $scope.nextLoading = false;

        }).catch(function(response) {
            TopAlert.add("Failed to get next conversion jobs", "error");
            $scope.nextLoading = false;
        });
    }

    /**
     * Smart table pipe function for finished conversions
     * @param {*} tableState
     */
    vm.finishedPipe = function(tableState) {
        $scope.finishedLoading = true;
        $http.get(appConfig.djangoUrl+"conversion-jobs/", { params: {end_date__isnull: false}}).then(function(response) {
            vm.finishedTableState = tableState;
            vm.finished = response.data;
            $scope.finishedLoading = false;

        }).catch(function(response) {
            TopAlert.add("Failed to get finished conversion jobs", "error");
            $scope.finishedLoading = false;
        })
    }
    function guid() {
        function s4() {
          return Math.floor((1 + Math.random()) * 0x10000)
            .toString(16)
            .substring(1);
        }
        return s4() + s4() + '-' + s4() + '-' + s4() + '-' +
          s4() + '-' + s4() + s4() + s4();
      }
    /**
     * Run conversion rule now
     * @param {Object} conversion
     */
    vm.runJob = function(job) {
        $http({
            url: appConfig.djangoUrl+"conversion-jobs/"+job.id+"/run/",
            method: "POST",
        }).then(function(response) {
            TopAlert.add("Running conversion job", "success");
        }).catch(function(response) {
            TopAlert.add(response.data.detail, "error");
        })
    }

    /*
     * Array containing chosen(checked) conversion rules to use
     * as filter for the other conversion tables
     */
    vm.ruleFilters = [];

    /**
     * Add chosen conversion rule to list of filters or remove it.
     * Connected to apprailsal rule table checkbox
     * @param {Object} rule
     */
    vm.useAsFilter = function(rule) {
        if(!vm.ruleFilters.includes(rule.id)) {
            rule.used_as_filter = true;
            vm.ruleFilters.push(rule.id);
        } else {
            vm.ruleFilters.splice(vm.ruleFilters.indexOf(rule.id), 1);
            rule.used_as_filter = false;
        }
    }
    /**
     * Show conversion report
     * @param {Object} conversion
     */
    vm.showReport = function(conversion) {
        var file = $sce.trustAsResourceUrl(appConfig.djangoUrl+"conversion-jobs/"+conversion.id+"/report/");
        $window.open(file, '_blank');
    }

    /**
     * MODALS
     */

    vm.previewModal = function(job) {
        var modalInstance = $uibModal.open({
            animation: true,
            ariaLabelledBy: 'modal-title',
            ariaDescribedBy: 'modal-body',
            templateUrl: 'static/frontend/views/preview_conversion_modal.html',
            controller: 'ConversionModalInstanceCtrl',
            controllerAs: '$ctrl',
            resolve: {
                data: {
                    preview: true,
                    job: job
                }
            }
        });
        modalInstance.result.then(function (data, $ctrl) {
            vm.runJob(job);
            vm.rulePipe(vm.ruleTableState);
            vm.nextPipe(vm.nextTableState);
            vm.ongoingPipe(vm.ongoingTableState);
            vm.finishedPipe(vm.finishedTableState);
        }, function () {
            $log.info('modal-component dismissed at: ' + new Date());
        });
    }

    vm.createRuleModal = function() {
        var modalInstance = $uibModal.open({
            animation: true,
            ariaLabelledBy: 'modal-title',
            ariaDescribedBy: 'modal-body',
            templateUrl: 'static/frontend/views/create_conversion_modal.html',
            controller: 'ConversionModalInstanceCtrl',
            controllerAs: '$ctrl',
            resolve: {
                data: {}
            }
        });
        modalInstance.result.then(function (data, $ctrl) {
            vm.rulePipe(vm.ruleTableState);
        }, function () {
            $log.info('modal-component dismissed at: ' + new Date());
        });
    }

    vm.ruleModal = function(rule) {
        var modalInstance = $uibModal.open({
            animation: true,
            ariaLabelledBy: 'modal-title',
            ariaDescribedBy: 'modal-body',
            templateUrl: 'static/frontend/views/conversion_rule_modal.html',
            controller: 'ConversionModalInstanceCtrl',
            controllerAs: '$ctrl',
            resolve: {
                data: {
                    rule: rule
                }
            }
        });
        modalInstance.result.then(function (data, $ctrl) {
        }, function () {
            $log.info('modal-component dismissed at: ' + new Date());
        });
    }

    vm.ongoingModal = function(conversion) {
        var modalInstance = $uibModal.open({
            animation: true,
            ariaLabelledBy: 'modal-title',
            ariaDescribedBy: 'modal-body',
            templateUrl: 'static/frontend/views/conversion_modal.html',
            controller: 'ConversionModalInstanceCtrl',
            controllerAs: '$ctrl',
            resolve: {
                data: {
                    conversion: conversion,
                    state: "Ongoing"
                }
            }
        });
        modalInstance.result.then(function (data, $ctrl) {
        }, function () {
            $log.info('modal-component dismissed at: ' + new Date());
        });
    }

    vm.nextModal = function(conversion) {
        var modalInstance = $uibModal.open({
            animation: true,
            ariaLabelledBy: 'modal-title',
            ariaDescribedBy: 'modal-body',
            templateUrl: 'static/frontend/views/conversion_modal.html',
            controller: 'ConversionModalInstanceCtrl',
            controllerAs: '$ctrl',
            resolve: {
                data: {
                    conversion: conversion,
                    state: "Next"
                }
            }
        });
        modalInstance.result.then(function (data, $ctrl) {
        }, function () {
            $log.info('modal-component dismissed at: ' + new Date());
        });
    }

    vm.finishedModal = function(conversion) {
        var modalInstance = $uibModal.open({
            animation: true,
            ariaLabelledBy: 'modal-title',
            ariaDescribedBy: 'modal-body',
            templateUrl: 'static/frontend/views/conversion_modal.html',
            controller: 'ConversionModalInstanceCtrl',
            controllerAs: '$ctrl',
            resolve: {
                data: {
                    conversion: conversion,
                    state: "Finished"
                }
            }
        });
        modalInstance.result.then(function (data, $ctrl) {
        }, function () {
            $log.info('modal-component dismissed at: ' + new Date());
        });
    }
    vm.removeConversionRuleModal = function(conversion) {
        var modalInstance = $uibModal.open({
            animation: true,
            ariaLabelledBy: 'modal-title',
            ariaDescribedBy: 'modal-body',
            templateUrl: 'static/frontend/views/remove_conversion_rule_modal.html',
            controller: 'ConversionModalInstanceCtrl',
            controllerAs: '$ctrl',
            resolve: {
                data: {
                    conversion: conversion,
                }
            }
        });
        modalInstance.result.then(function (data, $ctrl) {
            $http({
                url: appConfig.djangoUrl+"conversion-rules/"+conversion.id,
                method: "DELETE"
            }).then(function(response) {
                vm.rulePipe(vm.ruleTableState);
                TopAlert.add("conversion rule: "+conversion.name+" has been removed", "success");
            }).catch(function(response) {
                TopAlert.add("conversion rule could not be removed", "errorepp");
            })
        }, function () {
            $log.info('modal-component dismissed at: ' + new Date());
        });
    }
});
