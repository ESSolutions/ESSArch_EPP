angular.module('essarch.controllers').controller('DeliveryModalInstanceCtrl', [
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
    $ctrl.delivery = {};
    $ctrl.$onInit = function() {
      if (!data.remove) {
        if (data.delivery) {
          $ctrl.delivery = angular.copy(data.delivery);
          $ctrl.delivery.type = angular.copy(data.delivery.type.id);
        }
        $ctrl.getDeliveryTypes().then(function(response) {
          $ctrl.buildForm();
        })
      } else {
        if (data.delivery) {
          $ctrl.delivery = angular.copy(data.delivery);
        }
      }
    };

    $ctrl.getDeliveryTypes = function(search) {
      return $http
        .get(appConfig.djangoUrl + 'delivery-types/')
        .then(function(response) {
          $ctrl.deliveryTypes = response.data;
          return response.data;
        });
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
        {
          type: 'select',
          key: 'type',
          templateOptions: {
            required: true,
            label: $translate.instant('TYPE'),
            labelProp: 'name',
            valueProp: 'id',
            options: $ctrl.deliveryTypes,
            notNull: true,
          },
          defaultValue: $ctrl.deliveryTypes.length > 0 ? $ctrl.deliveryTypes[0].id : null,
        },
        {
          type: 'textarea',
          key: 'description',
          templateOptions: {
            required: true,
            label: $translate.instant('DESCRIPTION'),
            rows: 3,
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
      $ctrl.creating = true;
      $rootScope.skipErrorNotification = true;
      $http({
        url: appConfig.djangoUrl + 'deliveries/',
        method: 'POST',
        data: $ctrl.delivery,
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
        url: appConfig.djangoUrl + 'deliveries/' + data.delivery.id + '/',
        method: 'PATCH',
        data: Utils.getDiff(data.delivery, $ctrl.delivery, {map: {type: 'id'}}),
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
        .delete(appConfig.djangoUrl + 'deliveries/' + $ctrl.delivery.id)
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
