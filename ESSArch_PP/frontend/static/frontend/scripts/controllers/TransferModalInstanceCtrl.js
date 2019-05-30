angular.module('essarch.controllers').controller('TransferModalInstanceCtrl', [
  'appConfig',
  '$http',
  '$translate',
  'data',
  '$uibModalInstance',
  '$scope',
  'EditMode',
  'Utils',
  '$rootScope',
  function(appConfig, $http, $translate, data, $uibModalInstance, $scope, EditMode, Utils, $rootScope) {
    var $ctrl = this;
    $ctrl.transfer = {};
    $ctrl.$onInit = function() {
      if (!data.remove) {
        if (data.transfer) {
          $ctrl.transfer = angular.copy(data.transfer);
        }
        $ctrl.buildForm();
      } else {
        if (data.transfer) {
          $ctrl.transfer = angular.copy(data.transfer);
        }
      }
    };


    $ctrl.buildForm = function() {
      $ctrl.fields = [
        {
          type: 'input',
          key: 'name',
          templateOptions: {
            label: $translate.instant('NAME'),
            required: true,
          },
        },
      ];
    };

    $ctrl.cancel = function() {
      EditMode.disable();
      $uibModalInstance.dismiss('cancel');
    };
    $ctrl.create = function() {
      if ($ctrl.form.$invalid) {
        $ctrl.form.$setSubmitted();
        return;
      }
      $ctrl.transfer.delivery = angular.copy(data.delivery.id);
      $ctrl.creating = true;
      $rootScope.skipErrorNotification = true;
      $http({
        url: appConfig.djangoUrl + 'transfers/',
        method: 'POST',
        data: $ctrl.transfer,
      })
        .then(function(response) {
          $ctrl.creating = false;
          EditMode.disable();
          $uibModalInstance.close(response.data);
        })
        .catch(function(response) {
          $ctrl.nonFieldErrors = response.data.non_field_errors;
          $ctrl.creating = false;
        });
    };

    $ctrl.save = function() {
      if ($ctrl.form.$invalid) {
        $ctrl.form.$setSubmitted();
        return;
      }
      $ctrl.saving = true;
      $rootScope.skipErrorNotification = true;
      $http({
        url: appConfig.djangoUrl + 'transfers/' + data.transfer.id + '/',
        method: 'PATCH',
        data: Utils.getDiff(data.transfer, $ctrl.transfer, {map: {type: 'id'}}),
      })
        .then(function(response) {
          $ctrl.saving = false;
          EditMode.disable();
          $uibModalInstance.close(response.data);
        })
        .catch(function() {
          $ctrl.nonFieldErrors = response.data.non_field_errors;
          $ctrl.saving = false;
        });
    };

    $ctrl.remove = function() {
      $ctrl.removing = true;
      $rootScope.skipErrorNotification = true;
      $http
        .delete(appConfig.djangoUrl + 'transfers/' + $ctrl.transfer.id)
        .then(function(response) {
          $ctrl.removing = false;
          EditMode.disable();
          $uibModalInstance.close('removed');
        })
        .catch(function(response) {
          $ctrl.nonFieldErrors = response.data.non_field_errors;
          $ctrl.removing = false;
        });
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
  },
]);
