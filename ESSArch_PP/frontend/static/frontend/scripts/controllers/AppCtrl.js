angular.module('essarch.controllers').controller('AppCtrl', function($rootScope, $scope, $uibModal, $log, PermPermissionStore) {
    var vm = this;
    var questionMark = 187;
    vm.questionMarkListener = function(e) {
        if(e.shiftKey) {
            $('#list-view *').attr('UNSELECTABLE', 'on');
            $("#list-view").css(
                {
                    '-moz-user-select': 'none',
                    '-o-user-select': 'none',
                    '-khtml-user-select': 'none',
                    '-webkit-user-select': 'none',
                    '-ms-user-select': 'none',
                    'user-select': 'none'
                }
            );
            if(e.keyCode == questionMark) {
                $scope.keyboardShortcutModal();
            }
        }
    }

    vm.keyUpListener = function(e) {
        if(e.keyCode == 16) {
            $('#list-view *').attr('UNSELECTABLE', 'off');
            $("#list-view").css(
                {
                    '-moz-user-select': 'auto',
                    '-o-user-select': 'auto',
                    '-khtml-user-select': 'auto',
                    '-webkit-user-select': 'auto',
                    '-ms-user-select': 'auto',
                    'user-select': 'auto'
                }
            );
        }
    }

    $scope.checkPermission = function(permissionName) {
        return !angular.isUndefined(PermPermissionStore.getPermissionDefinition(permissionName));
    };

    //Create and show modal for keyboard shortcuts
    $scope.keyboardShortcutModal = function () {
        var modalInstance = $uibModal.open({
            animation: true,
            ariaLabelledBy: 'modal-title',
            ariaDescribedBy: 'modal-body',
            templateUrl: 'static/frontend/views/keyboard_shortcuts_modal.html',
            controller: 'ModalInstanceCtrl',
            controllerAs: '$ctrl',
            resolve: {
                data: {}
            }
        })
        modalInstance.result.then(function (data) {
        }, function () {
            $log.info('modal-component dismissed at: ' + new Date());
        });
    }

    $rootScope.mapStepStateProgress = function(row) {
        var property = angular.isUndefined(row.step_state) ? 'status' : 'step_state';
        switch (row[property]) {
            case 'SUCCESS':
                return 'success';
            case 'FAILURE':
                return 'danger';
            case 'STARTED':
                return 'warning';
            default:
                return 'warning';
        }
    }
});
