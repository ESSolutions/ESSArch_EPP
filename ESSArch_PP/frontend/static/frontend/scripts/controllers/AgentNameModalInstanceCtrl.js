angular
  .module('essarch.controllers')
  .controller('AgentNameModalInstanceCtrl', function(
    $uibModalInstance,
    $scope,
    $translate,
    $http,
    appConfig,
    data,
    EditMode
  ) {
    var $ctrl = this;
    $ctrl.name;
    $ctrl.nameTemplate = {
      part: null,
      main: null,
      description: null,
      start_date: null,
      end_date: null,
      type: null,
      certainty: null,
    };
    $ctrl.resetName = function() {
      $ctrl.name = angular.copy($ctrl.nameTemplate);
    };

    $ctrl.$onInit = function() {
      return $http({
        url: appConfig.djangoUrl + 'agents/',
        method: 'OPTIONS',
      }).then(function(response) {
        $ctrl.options = {names: {type: response.data.actions.POST.names.child.children.type}};
        EditMode.enable();
        if (data.name) {
          data.name.type = data.name.type.id;
          $ctrl.name = angular.copy(data.name);
        } else {
          $ctrl.resetName();
        }
      });
    };
    $ctrl.add = function() {
      $ctrl.adding = true;
      var names = angular.copy(data.agent.names);
      names.forEach(function(x) {
        x.type = x.type.id;
      });
      $http({
        url: appConfig.djangoUrl + 'agents/' + data.agent.id + '/',
        method: 'PATCH',
        data: {names: [$ctrl.name].concat(names)},
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
      var names = angular.copy(data.agent.names);
      names.forEach(function(x, idx, array) {
        if (typeof x.type === 'object') {
          x.type = x.type.id;
        }
        if (x.id === $ctrl.name.id) {
          array[idx] = $ctrl.name;
        }
      });
      $http({
        url: appConfig.djangoUrl + 'agents/' + data.agent.id + '/',
        method: 'PATCH',
        data: {names: names},
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
        }
      }
    });
  });
