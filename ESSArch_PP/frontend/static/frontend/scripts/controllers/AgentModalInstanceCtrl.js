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
      part: '',
      main: '',
      description: '',
      start_date: null,
      end_date: null,
      type: 1,
      certainty: null,
    };
    $ctrl.nameFields = [];
    $ctrl.basicFields = [];
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
      if (data.agent) {
        return $http({
          url: appConfig.djangoUrl + 'agents/',
          method: 'OPTIONS',
        }).then(function(response) {
          $ctrl.agent = angular.copy(data.agent);
          $ctrl.agent.ref_code = data.agent.ref_code.id;
          angular.forEach(response.data.actions.POST, function(value, key) {
            if (!angular.isUndefined(value.choices) && value.choices.length > 0) {
              $ctrl.options[key] = value;
              if (key === 'language') {
                $ctrl.sortLanguages();
              }
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
          $ctrl.buildTypeField($ctrl.agent).then(function(typeField) {
            $ctrl.loadBasicFields();
            $ctrl.basicFields.unshift(typeField);
          })
        });
      } else {
        $ctrl.buildAgentModel().then(function(model) {
          $ctrl.agent = model;
          $ctrl.buildTypeField($ctrl.agent).then(function(typeField) {
            typeField.templateOptions.onChange = function($modelValue) {
              if ($modelValue && $modelValue.cpf && $modelValue.cpf === 'corporatebody') {
                $ctrl.authName.part = '';
              }
              $ctrl.loadForms();
            };
            $ctrl.typeField = [typeField];
          })
        });
      }
      EditMode.enable();
    };

    $ctrl.buildTypeField = function(agent) {
      return $http.get(appConfig.djangoUrl + 'agent-types/', {params: {pager: 'none'}}).then(function(response) {
        var options = angular.copy(response.data);
        options.forEach(function(x) {
          x.name = x.main_type.name;
          if(x.id === agent.type.id) {
            agent.type = x;
          }
        })
        var type = {
          type: 'select',
          key: 'type',
          templateOptions: {
            options: options,
            getTypeName: function(type) {
              return type.main_type.name + (type.sub_type !== null && type.sub_type !== '' ? ' (' + type.sub_type + ')' : '');
            },
            ngOptions: 'to.getTypeName(x) for x in to.options',
            label: $translate.instant('TYPE'),
            required: true,
            notNull: true,
          },
        };
        return type;
      })
    };

    $ctrl.loadForms = function() {
      $ctrl.nameFields = [];
      $ctrl.basicFields = [];
      $ctrl.loadNameForm();
      $ctrl.loadBasicFields();
    }

    $ctrl.loadNameForm = function() {
      $ctrl.nameFields = [];
      if ($ctrl.agent.type && $ctrl.agent.type.cpf && $ctrl.agent.type.cpf !== 'corporatebody') {
        $ctrl.nameFields.push({
          className: 'row m-0',
          fieldGroup: [
            {
              className: 'col-xs-12 col-sm-6 px-0 pr-md-base',
              type: 'input',
              key: 'part',
              templateOptions: {
                label: $translate.instant('ACCESS.PART'),
              },
            },
            {
              className: 'col-xs-12 col-sm-6 px-0 pl-md-base',
              type: 'input',
              key: 'main',
              templateOptions: {
                label: $translate.instant('ACCESS.MAIN'),
                required: true,
              },
            },
          ],
        });
      } else {
        $ctrl.nameFields.push({
          type: 'input',
          key: 'main',
          templateOptions: {
            label: $translate.instant('NAME'),
            required: true,
          },
        });
      }

      $ctrl.nameFields = $ctrl.nameFields.concat([
        {
          className: 'row m-0',
          fieldGroup: [
            {
              className: 'col-xs-12 col-sm-6 px-0 pr-md-base',
              type: 'datepicker',
              key: 'start_date',
              templateOptions: {
                label: $translate.instant('ACCESS.VALID_DATE_START'),
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
          type: 'select',
          key: 'certainty',
          templateOptions: {
            options: [
              {value: true, display_name: $translate.instant('ACCESS.SURE')},
              {value: false, display_name: $translate.instant('ACCESS.UNSURE')},
            ],
            valueProp: 'value',
            labelProp: 'display_name',
            label: $translate.instant('ACCESS.CERTAINTY'),
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
      ]);
    };

    $ctrl.loadBasicFields = function() {
      $ctrl.basicFields = [
        {
          className: 'row m-0',
          fieldGroup: [
            {
              className: 'col-xs-12 col-sm-6 px-0 pr-md-base',
              type: 'datepicker',
              key: 'start_date',
              templateOptions: {
                label: $translate.instant('START_DATE'),
                appendToBody: false,
                dateFormat: 'YYYY-MM-DD',
              },
            },
            {
              className: 'col-xs-12 col-sm-6 px-0 pl-md-base',
              type: 'datepicker',
              key: 'end_date',
              templateOptions: {
                label: $translate.instant('END_DATE'),
                appendToBody: false,
                dateFormat: 'YYYY-MM-DD',
              },
            },
          ],
        },
        {
          type: 'select',
          key: 'level_of_detail',
          templateOptions: {
            options: $ctrl.options.level_of_detail.choices,
            valueProp: 'value',
            labelProp: 'display_name',
            label: $translate.instant('ACCESS.LEVEL_OF_DETAIL'),
            defaultValue: $ctrl.options.level_of_detail.choices[0].value,
            required: true,
            notNull: true,
          },
        },
        {
          type: 'select',
          key: 'script',
          templateOptions: {
            options: $ctrl.options.script.choices,
            valueProp: 'value',
            labelProp: 'display_name',
            label: $translate.instant('ACCESS.SCRIPT'),
            defaultValue: $ctrl.options.script.choices[0].value,
            required: true,
            notNull: true,
          },
          hideExpression: 'true',
        },
        {
          type: 'select',
          key: 'language',
          templateOptions: {
            options: $ctrl.options.language.choices,
            valueProp: 'value',
            labelProp: 'display_name',
            label: $translate.instant('ACCESS.LANGUAGE'),
            defaultValue: $ctrl.options.language.choices[0].value,
            required: true,
            notNull: true,
          },
          hideExpression: 'true',
        },
        {
          type: 'select',
          key: 'record_status',
          templateOptions: {
            options: $ctrl.options.record_status.choices,
            valueProp: 'value',
            labelProp: 'display_name',
            label: $translate.instant('ACCESS.RECORD_STATUS'),
            defaultValue: $ctrl.options.record_status.choices[0].value,
            required: true,
            notNull: true,
          },
          hideExpression: 'true',
        },
        {
          type: 'select',
          key: 'ref_code',
          templateOptions: {
            options: $ctrl.options.ref_code.choices,
            valueProp: 'value',
            labelProp: 'display_name',
            label: $translate.instant('ACCESS.REFERENCE_CODE'),
            defaultValue: $ctrl.options.ref_code.choices[0].value,
            required: true,
            notNull: true,
          },
        },
        {
          type: 'datepicker',
          key: 'create_date',
          templateOptions: {
            label: $translate.instant('CREATE_DATE'),
            appendToBody: false,
            required: true,
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
      $ctrl.agent.type = $ctrl.agent.type.id;
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
      if ($ctrl.form.$invalid) {
        $ctrl.form.$setSubmitted();
        return;
      }
      $ctrl.agent.type = $ctrl.agent.type.id;
      angular.forEach($ctrl.agent, function(value, key) {
        if (angular.isArray(value)) {
          delete $ctrl.agent[key];
        }
      });
      $ctrl.saving = true;
      $http({
        url: appConfig.djangoUrl + 'agents/' + data.agent.id + '/',
        method: 'PATCH',
        data: $ctrl.agent,
      })
        .then(function(response) {
          $ctrl.saving = false;
          EditMode.disable();
          $uibModalInstance.close(response.data);
        })
        .catch(function() {
          $ctrl.saving = false;
        });
    };

    $ctrl.remove = function() {
      $ctrl.removing = true;
      $http
        .delete(appConfig.djangoUrl + 'agents/' + $ctrl.agent.id)
        .then(function(response) {
          $ctrl.removing = false;
          EditMode.disable();
          $uibModalInstance.close('removed');
        })
        .catch(function() {
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
  });
