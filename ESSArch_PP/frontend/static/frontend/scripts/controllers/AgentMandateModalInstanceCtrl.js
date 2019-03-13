angular
  .module('essarch.controllers')
  .controller('AgentMandateModalInstanceCtrl', function(
    $uibModalInstance,
    $scope,
    $translate,
    $http,
    appConfig,
    data,
    EditMode
  ) {
    var $ctrl = this;
    $ctrl.mandate;
    $ctrl.mandateTemplate = {
      part: null,
      main: null,
      description: null,
      start_date: null,
      end_date: null,
      type: 1,
      certainty: null,
    };
    $ctrl.resetMandate = function() {
      $ctrl.mandate = angular.copy($ctrl.mandateTemplate);
    };

    $ctrl.$onInit = function() {
      return $http({
        url: appConfig.djangoUrl + 'agents/',
        method: 'OPTIONS',
      }).then(function(response) {
        $ctrl.options = {mandates: {type: response.data.actions.POST.mandates.child.children.type}};
        EditMode.enable();
        if (data.mandate) {
          data.mandate.type = data.mandate.type.id;
          $ctrl.mandate = angular.copy(data.mandate);
        } else {
          $ctrl.resetMandate();
        }
      });
    };
    $ctrl.add = function() {
      $ctrl.adding = true;
      var mandates = angular.copy(data.agent.mandates);
      mandates.forEach(function(x) {
        x.type = x.type.id;
      });
      $http({
        url: appConfig.djangoUrl + 'agents/' + data.agent.id + '/',
        method: 'PATCH',
        data: {mandates: [$ctrl.mandate].concat(mandates)},
      })
        .then(function(response) {
          $ctrl.adding = false;
          EditMode.disable();
          $uibModalInstance.close(response.data);
        })
        .catch(function(response) {
          $ctrl.adding = false;
        });
    };
    $ctrl.save = function() {
      $ctrl.saving = true;
      var mandates = angular.copy(data.agent.mandates);
      mandates.forEach(function(x, idx, array) {
        if (typeof x.type === 'object') {
          x.type = x.type.id;
        }
        if (x.id === $ctrl.mandate.id) {
          array[idx] = $ctrl.mandate;
        }
      });
      $http({
        url: appConfig.djangoUrl + 'agents/' + data.agent.id + '/',
        method: 'PATCH',
        data: {mandates: mandates},
      }).then(function(response) {
        $ctrl.saving = false;
        EditMode.disable();
        $uibModalInstance.close(response.data);
      }).catch(function() {
        $ctrl.saving = false;
      })
    };
    $ctrl.cancel = function() {
      EditMode.disable();
      $uibModalInstance.dismiss('cancel');
    };

    $scope.$on('modal.closing', function(event, reason, closed) {
      if (reason === 'cancel' || reason === 'backdrop click' || reason === 'escape key press') {
        var message = $translate.instant('UNSAVED_DATA_WARNING');
        if (!confirm(message)) {
          event.preventDefault();
        } else {
          EditMode.disable();
        }
      }
    });
  });
