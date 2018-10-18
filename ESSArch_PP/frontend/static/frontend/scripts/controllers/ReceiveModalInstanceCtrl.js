angular.module('essarch.controllers').controller('ReceiveModalInstanceCtrl', function (Notifications, $uibModalInstance, $scope, $rootScope,  djangoAuth, data, Requests, $translate, IPReception) {
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
});
