angular.module('essarch.controllers').controller('AgentModalInstanceCtrl', function($uibModalInstance, data) {
  var $ctrl = this;
  $ctrl.options = {
    type: [
      {main_type: 'Pastorat', id: '1'},
      {main_type: 'Församling', id: '2'},
      {main_type: 'Stift', id: '3'},
      {main_type: 'Nationellt organ', id: '4'},
    ],
  };
  $ctrl.$onInit = function() {
    if (!angular.isUndefined(data.agent) && data.agent !== null) {
      $ctrl.agent = angular.copy(data.agent);
    } else {
      $ctrl.agent = {
        name: null,
        type: null,
        start_date: null,
        end_date: null,
        notes: null,
      };
    }
  };
  $ctrl.cancel = function() {
    $uibModalInstance.dismiss('cancel');
  };
  $ctrl.create = function() {
    $uibModalInstance.close(angular.extend($ctrl.agent, {id: Math.floor(Math.random() * Math.floor(20))}));
  };
  $ctrl.save = function() {
    $uibModalInstance.close($ctrl.agent);
  };
});
