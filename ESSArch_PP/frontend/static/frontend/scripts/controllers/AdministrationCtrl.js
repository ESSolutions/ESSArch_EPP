angular.module('myApp').controller('AdministrationCtrl', function($state, myService) {
    var vm = this;
    vm.checkPermissions = function(permissions) {
        return myService.checkPermissions(permissions);
    }
    vm.$onInit = function () {
        if (vm.checkPermissions(['storage.storage_management'])) {
            $state.go('home.administration.mediaInformation');
        } else {
            if (vm.checkPermissions(['storage.storage_management'])) {
                $state.go('home.administration.robotInformation')
            } else {
                if (vm.checkPermissions(['storage.storage_management'])) {
                    $state.go('home.administration.queues');
                } else {
                    if (vm.checkPermissions(['storage.storage_migration'])) {
                        $state.go('home.administration.storageMigration')
                    } else {
                        if (vm.checkPermissions(['storage.storage_maintenance'])) {
                            $state.go('home.administration.storageMaintenance');
                        } else {
                            throw new Error("State has no available substate");
                        }
                    }
                }
            }
        }
    }
});
