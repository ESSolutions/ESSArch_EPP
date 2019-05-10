angular
  .module('essarch.controllers')
  .controller('NodeLocationModalInstanceCtrl', function(
    $scope,
    data,
    $uibModalInstance,
    appConfig,
    $http,
    EditMode,
    Search,
    $translate
  ) {
    var $ctrl = this;
    $ctrl.location = null;

    $ctrl.$onInit = function() {
      EditMode.enable();
      if (!angular.isUndefined(data.node)) {
        $ctrl.node = angular.copy(data.node);
      }
      if (data.location !== null && !angular.isUndefined(data.location)) {
        $ctrl.location = angular.copy(data.location)
      }
    };

    $ctrl.save = function() {
      if ($ctrl.location === null) {
        $ctrl.nonFieldErrors = [$translate.instant('ACCESS.YOU_MUST_PICK_LOCATION')];
        return;
      }
      $ctrl.saving = true;
      Search.updateNode(data.node, {location: $ctrl.location.id})
        .then(function(response) {
          $ctrl.saving = false;
          EditMode.disable();
          $uibModalInstance.close('edited');
        })
        .catch(function(response) {
          $ctrl.nonFieldErrors = response.data.non_field_errors;
          $ctrl.saving = false;
        });
    };

    $ctrl.cancel = function() {
      EditMode.disable();
      $uibModalInstance.dismiss();
    };

    $scope.$on('modal.closing', function(event, reason, closed) {
      if (
        (data.allow_close === null || angular.isUndefined(data.allow_close) || data.allow_close !== true) &&
        (reason === 'cancel' || reason === 'backdrop click' || reason === 'escape key press')
      ) {
        var message = $translate.instant('UNSAVED_DATA_WARNING');
        if (!confirm(message)) {
          event.preventDefault();
        } else {
          EditMode.disable();
        }
      }
    });
  });
