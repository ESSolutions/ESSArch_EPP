angular.module('myApp').controller('AccessCtrl', function($state, myService) {
    var vm = this;
    vm.checkPermissions = function(permissions) {
        return myService.checkPermissions(permissions);
    }
    vm.$onInit = function () {
        if (vm.checkPermissions(['ip.get_from_storage', 'ip.get_tar_from_storage', 'ip.get_from_storage_as_new'])) {
            $state.go('home.access.accessIp');
        } else {
            if (vm.checkPermissions(['ip.move_from_ingest_workarea', 'ip.move_from_ingest_workarea'])) {
                $state.go('home.access.workarea')
            } else {
                if (vm.checkPermissions(['ip.diff-check', 'ip.preserve'])) {
                    $state.go('home.access.createDip');
                } else {
                    throw new Error("State has no available substate");
                }
            }
        }
    }
});