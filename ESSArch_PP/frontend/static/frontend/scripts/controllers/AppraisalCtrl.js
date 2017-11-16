angular.module('myApp').controller('AppraisalCtrl', function(ArchivePolicy, $scope, $controller, $rootScope, $cookies, $stateParams, appConfig, $http, $timeout, $uibModal, $log) {
    var vm = this;
    vm.rulesPerPage = 10;
    vm.ongoingPerPage = 10;
    vm.nextPerPage = 10;
    vm.finishedPerPage = 10;
    $scope.ruleLoading = false;
    $scope.ongoingLoading = false;
    $scope.nextLoading = false;
    $scope.finishedLoading = false;

    /**
     * Smart table pipe function for appraisal rules
     * @param {*} tableState
     */
    vm.rulePipe = function(tableState) {
        $scope.ruleLoading = true;
        $timeout(function() {

            vm.ruleTableState = tableState;
            vm.ruleFilters.forEach(function(x) {
                ruleset.forEach(function(rule) {
                    if(x == rule.id) {
                        rule.usedAsFilter = true;
                    }
                });
            });
            vm.rules = ruleset;
            $scope.ruleLoading = false;
        }, 200)
    }

    /**
     * Smart table pipe function for ongoing appraisals
     * @param {*} tableState
     */
    vm.ongoingPipe = function(tableState) {
        $scope.ongoingLoading = true;
        $timeout(function() {

            vm.ongoingTableState = tableState;
            vm.ongoing = ongoing;
            $scope.ongoingLoading = false;
        }, 400)
    }

    /**
     * Smart table pipe function for next appraisals
     * @param {*} tableState
     */
    vm.nextPipe = function(tableState) {
        $scope.nextLoading = true;
        $timeout(function() {

            vm.nextTableState = tableState;
            vm.next = next;
            $scope.nextLoading = false;
        }, 700)
    }

    /**
     * Smart table pipe function for finished appraisals
     * @param {*} tableState
     */
    vm.finishedPipe = function(tableState) {
        $scope.finishedLoading = true;
        $timeout(function() {

            vm.finishedTableState = tableState;
            vm.finished = finished;
            $scope.finishedLoading = false;
        }, 650)
    }

    /**
     * Run appraisal rule now
     * @param {Object} appraisal
     */
    vm.runNow = function(appraisal) {
        alert(appraisal.name + " is running!");
    }

    /*
     * Array containing chosen(checked) appraisal rules to use
     * as filter for the other appraisal tables
     */
    vm.ruleFilters = [];

    /**
     * Add chosen appraisal rule to list of filters or remove it.
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
     * Show appraisal report
     * @param {Object} appraisal
     */
    vm.showReport = function(appraisal) {
        console.log(appraisal.report);
    }

    /**
     * MODALS
     */

    vm.createRuleModal = function() {
        var modalInstance = $uibModal.open({
            animation: true,
            ariaLabelledBy: 'modal-title',
            ariaDescribedBy: 'modal-body',
            templateUrl: 'static/frontend/views/create_appraisal_modal.html',
            controller: 'AppraisalModalInstanceCtrl',
            controllerAs: '$ctrl',
            resolve: {
                data: {}
            }
        });
        modalInstance.result.then(function (data, $ctrl) {
            ruleset.push(angular.extend({id: Math.random()}, data));
        }, function () {
            $log.info('modal-component dismissed at: ' + new Date());
        });
    }

    vm.ruleModal = function(rule) {
        var modalInstance = $uibModal.open({
            animation: true,
            ariaLabelledBy: 'modal-title',
            ariaDescribedBy: 'modal-body',
            templateUrl: 'static/frontend/views/appraisal_rule_modal.html',
            controller: 'AppraisalModalInstanceCtrl',
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

    vm.ongoingModal = function(appraisal) {
        var modalInstance = $uibModal.open({
            animation: true,
            ariaLabelledBy: 'modal-title',
            ariaDescribedBy: 'modal-body',
            templateUrl: 'static/frontend/views/appraisal_modal.html',
            controller: 'AppraisalModalInstanceCtrl',
            controllerAs: '$ctrl',
            resolve: {
                data: {
                    appraisal: appraisal,
                    state: "Ongoing"
                }
            }
        });
        modalInstance.result.then(function (data, $ctrl) {
        }, function () {
            $log.info('modal-component dismissed at: ' + new Date());
        });
    }

    vm.nextModal = function(appraisal) {
        var modalInstance = $uibModal.open({
            animation: true,
            ariaLabelledBy: 'modal-title',
            ariaDescribedBy: 'modal-body',
            templateUrl: 'static/frontend/views/appraisal_modal.html',
            controller: 'AppraisalModalInstanceCtrl',
            controllerAs: '$ctrl',
            resolve: {
                data: {
                    appraisal: appraisal,
                    state: "Next"
                }
            }
        });
        modalInstance.result.then(function (data, $ctrl) {
        }, function () {
            $log.info('modal-component dismissed at: ' + new Date());
        });
    }

    vm.finishedModal = function(appraisal) {
        var modalInstance = $uibModal.open({
            animation: true,
            ariaLabelledBy: 'modal-title',
            ariaDescribedBy: 'modal-body',
            templateUrl: 'static/frontend/views/appraisal_modal.html',
            controller: 'AppraisalModalInstanceCtrl',
            controllerAs: '$ctrl',
            resolve: {
                data: {
                    appraisal: appraisal,
                    state: "Finished"
                }
            }
        });
        modalInstance.result.then(function (data, $ctrl) {
        }, function () {
            $log.info('modal-component dismissed at: ' + new Date());
        });
    }

    /**
     * Test data
     */
    var ruleset = [
        { id: 1, name: "Rule 1", frequency: "24h", type: "Arkivobjekt" },
        { id: 2, name: "Rule 2", frequency: "1 week", type: "Metadata" },
        { id: 3, name: "Rule 4", frequency: "10 years", type: "Metadata" },
        { id: 4, name: "Rule 3", frequency: "24h", type: "Arkivobjekt" },
        { id: 5, name: "Rule 6", frequency: "1 year", type: "Metadata" },
        { id: 6, name: "Rule 5", frequency: "2h", type: "Arkivobjekt" },
        { id: 7, name: "Rule 7", frequency: "Manual", type: "Arkivobjekt" }
    ];
    var ongoing =  [
        { id: 1, start: new Date("2017-11-10 12:53:00"), rule: ruleset[0] },
        { id: 2, start: new Date(), rule: ruleset[2] }
    ];

    var next =  [
        { id: 3, start: new Date("2017-11-10 12:53:00"), rule: ruleset[1] },
        { id: 4, start: new Date(), rule: ruleset[3] }
    ];

    var finished =  [
        { id: 5, start: new Date("2017-11-10 12:53:00"), end: new Date("2017-11-10 15:50:22"), report: "gallring_5.pdf", rule: ruleset[0]},
        { id: 6, start: new Date("2017-11-14 15:53:26"), end: new Date("2017-11-15 15:01:06"), report: "gallring_6.pdf", rule: ruleset[1]}
    ];
});
