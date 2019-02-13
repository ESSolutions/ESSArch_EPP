angular.module('essarch.controllers').controller('ArchiveCreatorModalInstanceCtrl', function($uibModalInstance, data) {
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
    if (!angular.isUndefined(data.creator) && data.creator !== null) {
      $ctrl.creator = angular.copy(data.creator);
    } else {
      $ctrl.creator = {
        name: null,
        type: null,
        startDate: null,
        endDate: null,
        notes: null,
      };
    }
  };
  $ctrl.cancel = function() {
    $uibModalInstance.dismiss('cancel');
  };
  $ctrl.create = function() {
    // Create archive creator
    $uibModalInstance.close(angular.extend($ctrl.creator, {id: Math.floor(Math.random() * Math.floor(20))}));
  };
  $ctrl.save = function() {
    $uibModalInstance.close($ctrl.creator);
  };
});
