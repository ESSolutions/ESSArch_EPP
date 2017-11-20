angular.module('myApp').controller('AppraisalCtrl', function(ArchivePolicy, $scope, $controller, $rootScope, $cookies, $stateParams, appConfig, $http, $timeout, $uibModal, $log, $sce, $window, TopAlert, $filter) {
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
     * Run appraisal rule now
     * @param {Object} appraisal
     */
    vm.runNow = function(appraisal) {
        var object = {
            id: guid(),
            start: new Date(),
            rule: appraisal
        };
        TopAlert.add(appraisal.name +", started at: "+$filter("date")(object.start, "yyyy-MM-dd HH:mm:ss"), "success");
        vm.ongoing.push(object);
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
        var file = $sce.trustAsResourceUrl("/static/frontend/gallringsrapport.pdf");
        $window.open(file, '_blank');
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
        { id: 'ad961193-6162-4871-9ceb-d464e2276586', name: "Gallring fakturor", frequency: "24h", type: "Arkivobjekt" },
        { id: 'b987a27f-a111-43d6-83cf-dbbab1a8de8c', name: "Gallring lönsespecefikationer", frequency: "1 week", type: "Metadata" },
        { id: '2a4ffd3e-8796-4040-a0ca-7a27420541f9', name: "Rule 4", frequency: "10 years", type: "Metadata" },
        { id: 'fc84bbef-7387-4528-b667-e24efa2940c4', name: "Rule 3", frequency: "24h", type: "Arkivobjekt" },
        { id: 'b53f58f5-b062-4f3d-9c01-31835c90b04c', name: "Rule 6", frequency: "1 year", type: "Metadata" },
        { id: '21fdd706-cbb5-40d5-897a-363939589db6', name: "Rule 5", frequency: "2h", type: "Arkivobjekt" },
        { id: '1bff3bd2-f7df-4555-b539-26c175ac216d', name: "Rule 7", frequency: "Manual", type: "Arkivobjekt" }
    ];
    var ongoing =  [
        { id: '7569aeb6-5601-47dc-96bd-219af2079dcb', start: new Date("2017-11-10 12:53:00"), rule: ruleset[0] },
        { id: '2621bced-ae07-492d-9428-2fed980e3ae8', start: new Date("2017-11-10 15:53:00"), rule: ruleset[2] }
    ];

    var next =  [
        { id: '7a77e432-abd8-4fee-af05-1343b721db52', start: new Date("2017-11-12 12:45:25"), rule: ruleset[1] },
        { id: '4e9728f9-4e15-4eb6-97da-8fdae209410e', start: new Date("2017-11-12 05:15:30"), rule: ruleset[3] }
    ];

    var finished =  [
        { id: '93abbe52-f79b-4b09-af2c-34c9ac20a04f', start: new Date("2017-11-9 12:58:03"), end: new Date("2017-11-9 12:59:58"), report: "gallring_93abbe52-f79b-4b09-af2c-34c9ac20a04f.pdf", rule: ruleset[0]},
        { id: 'a34dbf51-b4fa-409b-8039-b397b15d77c5', start: new Date("2017-11-9 15:18:26"), end: new Date("2017-11-9 15:25:01"), report: "gallring_a34dbf51-b4fa-409b-8039-b397b15d77c5.pdf", rule: ruleset[1]}
    ];
});
