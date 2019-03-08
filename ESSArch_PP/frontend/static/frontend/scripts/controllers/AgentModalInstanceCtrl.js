angular
  .module('essarch.controllers')
  .controller('AgentModalInstanceCtrl', function(
    $uibModalInstance,
    data,
    appConfig,
    $http,
    $scope,
    EditMode,
    $translate
  ) {
    var $ctrl = this;
    $ctrl.options = {};
    $ctrl.authName = {
      part: null,
      main: null,
      description: null,
      start_date: null,
      end_date: null,
      type: 1,
      certainty: null,
    };

    $ctrl.sortLanguages = function() {
      var swe, eng;
      $ctrl.options.language.choices.forEach(function(choice, idx, array) {
        if (choice.value === 'en') {
          eng = angular.copy(choice);
          array.splice(idx, 1);
        }
        if (choice.value === 'sv') {
          swe = angular.copy(choice);
          array.splice(idx, 1);
        }
      });
      $ctrl.options.language.choices.unshift(eng);
      $ctrl.options.language.choices.unshift(swe);
    };

    $ctrl.buildAgentModel = function() {
      return $http({
        url: appConfig.djangoUrl + 'agents/',
        method: 'OPTIONS',
      }).then(function(response) {
        var model = {};
        angular.forEach(response.data.actions.POST, function(value, key) {
          if (value.many) {
            model[key] = [];
          } else if (value.type === 'datetime') {
            model[key] = new Date();
          } else {
            model[key] = null;
          }
          if (!angular.isUndefined(value.choices) && value.choices.length > 0) {
            $ctrl.options[key] = value;
            if (key === 'language') {
              $ctrl.sortLanguages();
            }
            model[key] = value.choices[0].value;
          }
          if (!angular.isUndefined(value.child) && !angular.isUndefined(value.child.children)) {
            angular.forEach(value.child.children, function(nestedVal, nestedKey) {
              if (!angular.isUndefined(nestedVal.choices)) {
                $ctrl.options[key] = {
                  child: {
                    children: {},
                  },
                };
                $ctrl.options[key].child.children[nestedKey] = nestedVal;
              }
            });
          }
        });
        delete model.id;
        return model;
      });
    };

    $ctrl.$onInit = function() {
      if (!angular.isUndefined(data.agent) && data.agent !== null) {
        $ctrl.agent = angular.copy(data.agent);
      } else {
        $ctrl.buildAgentModel().then(function(model) {
          $ctrl.agent = model;
        });
      }
      EditMode.enable();
    };
    $ctrl.cancel = function() {
      EditMode.disable();
      $uibModalInstance.dismiss('cancel');
    };
    $ctrl.create = function() {
      $ctrl.creating = true;
      $ctrl.agent.names = [];
      $ctrl.agent.names.push($ctrl.authName);
      $http({
        url: appConfig.djangoUrl + 'agents/',
        method: 'POST',
        data: $ctrl.agent,
      })
        .then(function(response) {
          $ctrl.creating = false;
          EditMode.disable();
          $uibModalInstance.close(response.data);
        })
        .catch(function() {
          $ctrl.creating = false;
        });
    };
    $ctrl.save = function() {
      $uibModalInstance.close($ctrl.agent);
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
