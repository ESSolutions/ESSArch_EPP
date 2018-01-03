angular.module('myApp').controller('AppCtrl', function($rootScope, $scope, $uibModal, $log) {
    var vm = this;
    var questionMark = 187;
    vm.questionMarkListener = function(e) {
        if(e.keyCode == questionMark && e.shiftKey) {
            $scope.keyboardShortcutModal();
        }
    }

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
});
