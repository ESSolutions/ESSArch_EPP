angular
  .module('essarch.controllers')
  .controller('AgentMandateModalInstanceCtrl', function(
    $uibModalInstance,
    $scope,
    $translate,
    $http,
    appConfig,
    data,
    EditMode,
    $rootScope
  ) {
    var $ctrl = this;
    $ctrl.mandate;
    $ctrl.fields = [];
    $ctrl.mandateTemplate = {
      part: '',
      main: '',
      description: '',
      start_date: null,
      end_date: null,
      href: '',
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
          var mandate = angular.copy(data.mandate);
          mandate.type = data.mandate.type.id;
          $ctrl.mandate = angular.copy(mandate);
        } else {
          $ctrl.resetMandate();
        }
        $ctrl.loadForm();
      });
    };

    $ctrl.loadForm = function() {
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
            label: $translate.instant('TYPE'),
            options: $ctrl.options.mandates.type.choices,
            required: true,
            labelProp: 'display_name',
            valueProp: 'value',
            defaultValue:
              $ctrl.options.mandates.type.choices.length > 0 ? $ctrl.options.mandates.type.choices[0].value : null,
            notNull: true,
          },
        },
        {
          className: 'row m-0',
          fieldGroup: [
            {
              className: 'col-xs-12 col-sm-6 px-0 pr-md-base',
              type: 'datepicker',
              key: 'start_date',
              templateOptions: {
                label: $translate.instant('ACCESS.DECISION_DATE'),
                appendToBody: false,
                dateFormat: 'YYYY-MM-DD',
              },
            },
            {
              className: 'col-xs-12 col-sm-6 px-0 pl-md-base',
              type: 'datepicker',
              key: 'end_date',
              templateOptions: {
                label: $translate.instant('ACCESS.VALID_DATE_END'),
                appendToBody: false,
                dateFormat: 'YYYY-MM-DD',
              },
            },
          ],
        },
        {
          type: 'input',
          key: 'href',
          templateOptions: {
            label: $translate.instant('ACCESS.HREF'),
          },
        },
        {
          key: 'description',
          type: 'textarea',
          templateOptions: {
            label: $translate.instant('DESCRIPTION'),
            rows: 3,
          },
        },
      ];
    };

    $ctrl.add = function() {
      if ($ctrl.form.$invalid) {
        $ctrl.form.$setSubmitted();
        return;
      }
      $ctrl.adding = true;
      var mandates = angular.copy(data.agent.mandates);
      mandates.forEach(function(x) {
        if (typeof x.type === 'object') {
          x.type = angular.copy(x.type.id);
        }
      });
      $rootScope.skipErrorNotification = true;
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
          $ctrl.nonFieldErrors = response.data.non_field_errors;
          if(response.data.mandates) {
            if(angular.isArray($ctrl.nonFieldErrors)) {
              $ctrl.nonFieldErrors = $ctrl.nonFieldErrors.concat(response.data.mandates);
            } else {
              $ctrl.nonFieldErrors = response.data.mandates;
            }
          }
          $ctrl.adding = false;
        });
    };
    $ctrl.save = function() {
      if ($ctrl.form.$invalid) {
        $ctrl.form.$setSubmitted();
        return;
      }
      $ctrl.saving = true;
      var mandates = angular.copy(data.agent.mandates);
      mandates.forEach(function(x, idx, array) {
        if (typeof x.type === 'object') {
          x.type = angular.copy(x.type.id);
        }
        if (x.id === $ctrl.mandate.id) {
          array[idx] = $ctrl.mandate;
        }
      });
      $rootScope.skipErrorNotification = true;
      $http({
        url: appConfig.djangoUrl + 'agents/' + data.agent.id + '/',
        method: 'PATCH',
        data: {mandates: mandates},
      })
        .then(function(response) {
          $ctrl.saving = false;
          EditMode.disable();
          $uibModalInstance.close(response.data);
        })
        .catch(function() {
          $ctrl.nonFieldErrors = response.data.non_field_errors;
          if(response.data.mandates) {
            if(angular.isArray($ctrl.nonFieldErrors)) {
              $ctrl.nonFieldErrors = $ctrl.nonFieldErrors.concat(response.data.mandates);
            } else {
              $ctrl.nonFieldErrors = response.data.mandates;
            }
          }
          $ctrl.saving = false;
        });
    };

    $ctrl.remove = function() {
      $ctrl.removing = true;
      var toRemove = null;
      var mandates = angular.copy(data.agent.mandates);
      mandates.forEach(function(x, idx, array) {
        if (typeof x.type === 'object') {
          x.type = angular.copy(x.type.id);
        }
        if (x.id === $ctrl.mandate.id) {
          toRemove = idx;
        }
      });
      if (toRemove !== null) {
        mandates.splice(toRemove, 1);
      }
      $rootScope.skipErrorNotification = true;
      $http({
        url: appConfig.djangoUrl + 'agents/' + data.agent.id + '/',
        method: 'PATCH',
        data: {mandates: mandates},
      })
        .then(function(response) {
          $ctrl.removing = false;
          EditMode.disable();
          $uibModalInstance.close(response.data);
        })
        .catch(function() {
          $ctrl.nonFieldErrors = response.data.non_field_errors;
          if(response.data.mandates) {
            if(angular.isArray($ctrl.nonFieldErrors)) {
              $ctrl.nonFieldErrors = $ctrl.nonFieldErrors.concat(response.data.mandates);
            } else {
              $ctrl.nonFieldErrors = response.data.mandates;
            }
          }
          $ctrl.removing = false;
        });
    };

    $ctrl.cancel = function() {
      EditMode.disable();
      $uibModalInstance.dismiss('cancel');
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
  });
