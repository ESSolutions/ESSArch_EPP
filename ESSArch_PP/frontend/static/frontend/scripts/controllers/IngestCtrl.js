angular.module('myApp').controller('IngestCtrl', function($state, myService) {
    var vm = this;
    vm.checkPermissions = function(permissions) {
        return myService.checkPermissions(permissions);
    }
    vm.$onInit = function () {
        if (vm.checkPermissions(['ip.receive'])) {
            $state.go('home.ingest.reception');
        } else {
            if (vm.checkPermissions(['ip.preserve', 'ip.get_from_storage', 'ip.get_from_storage_as_new', 'ip.diff-check'])) {
                $state.go('home.ingest.ipApproval')
            } else {
                if (vm.checkPermissions(['ip.move_from_ingest_workarea', 'ip.move_from_ingest_workarea'])) {
                    $state.go('home.ingest.workarea');
                } else {
                    throw new Error("State has no available substate");
                }
            }
        }
    }
});