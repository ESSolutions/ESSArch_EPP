angular
  .module('essarch.controllers')
  .controller('PublishClassificationStructureCtrl', function($http, appConfig, $uibModalInstance, data) {
    var $ctrl = this;
    $ctrl.$onInit = function() {
      $ctrl.data = data;
    };
    $ctrl.publish = function() {
      $ctrl.publishing = true;
      $http({
        url: appConfig.djangoUrl + 'structures/' + data.structure.id + '/publish/',
        method: 'POST',
      })
        .then(function(response) {
          $ctrl.publishing = false;
          $uibModalInstance.close(response);
        })
        .catch(function() {
          $ctrl.publishing = false;
        });
    };
    $ctrl.cancel = function() {
      $uibModalInstance.dismiss('cancel');
    };
  });
