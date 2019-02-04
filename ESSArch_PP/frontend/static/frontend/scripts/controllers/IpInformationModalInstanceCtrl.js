angular
  .module('essarch.controllers')
  .controller('IpInformationModalInstanceCtrl', function(
    IP,
    $translate,
    $uibModalInstance,
    djangoAuth,
    appConfig,
    $http,
    data,
    $scope,
    Notifications
  ) {
    var $ctrl = this;
    $scope.angular = angular;
    $ctrl.editMode = {};
    $ctrl.ipModifications = {};

    $ctrl.$onInit = function() {
      $ctrl.initLoad = true;
      IP.get({id: data.ip.id})
        .$promise.then(function(resource) {
          $ctrl.ip = resource;
          IP.storageObjects({id: resource.id})
            .$promise.then(function(resource) {
              $ctrl.storageObjects = resource;
              $ctrl.initLoad = false;
            })
            .catch(function(response) {
              $ctrl.initLoad = false;
              Notifications.add('Could not get storage objects', 'error');
            });
        })
        .catch(function(response) {
          $ctrl.initLoad = false;
          Notifications.add('Could not get IP', 'error');
        });
    };

    $ctrl.editField = function(field) {
      $ctrl.editMode[field] = true;
    };

    $ctrl.closeIpEdit = function(field) {
      $ctrl.editMode[field] = false;
    };
    $ctrl.saveIpModifications = function(field) {
      IP.update({id: $ctrl.ip.id}, $ctrl.ipModifications).$promise.then(function(response) {
        Notifications.add('Updated!', 'error');
        $ctrl.editMode[field] = false;
      });
    };

    $ctrl.cancel = function() {
      $uibModalInstance.dismiss('cancel');
    };
  });
