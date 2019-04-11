angular
  .module('essarch.controllers')
  .controller('PublishClassificationStructureCtrl', function($http, appConfig, $uibModalInstance, data) {
    var $ctrl = this;
    $ctrl.$onInit = function() {
      $ctrl.data = data;
    };
    $ctrl.publish = function() {
      $http({
        url: appConfig.djangoUrl + 'structures/' + data.structure.id + '/publish/',
        method: 'POST',
      }).then(function(response) {
        $uibModalInstance.close(response);
      });
    };
    $ctrl.cancel = function() {
      $uibModalInstance.dismiss('cancel');
    };
  });
