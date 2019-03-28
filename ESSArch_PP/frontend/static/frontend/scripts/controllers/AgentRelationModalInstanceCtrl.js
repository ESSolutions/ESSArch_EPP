angular
  .module('essarch.controllers')
  .controller('AgentRelationModalInstanceCtrl', function(
    $uibModalInstance,
    appConfig,
    data,
    $http,
    EditMode,
    $scope,
    $translate
  ) {
    var $ctrl = this;
    $ctrl.relationTemplate = {
      type: 1,
      description: '',
      start_date: null,
      end_date: null,
      create_date: new Date(),
      revise_date: null,
      agent: null,
    };
    $ctrl.options = {};
    $ctrl.fields = [];
    $ctrl.getAuthorizedName = function(agent) {
      var name;
      agent.names.forEach(function(x) {
        x.full_name = (x.part !== null && x.part !== '' ? x.part + ', ' : '') + x.main;
        if (x.type.name.toLowerCase() === 'auktoriserad') {
          name = x;
          agent.full_name = (x.part !== null && x.part !== '' ? x.part + ', ' : '') + x.main;
        }
      });
      return name;
    };

    $ctrl.getAgents = function(search) {
      return $http({
        url: appConfig.djangoUrl + 'agents/',
        mathod: 'GET',
        params: {page: 1, page_size: 10, search: search},
      }).then(function(response) {
        response.data.forEach(function(agent) {
          agent.auth_name = $ctrl.getAuthorizedName(agent);
        });
        $ctrl.options.agents = response.data;
        return $ctrl.options.agents;
      });
    };
    $ctrl.data = data;
    $ctrl.$onInit = function() {
      if (data.agent) {
        $ctrl.agent = angular.copy(data.agent);
      }
      if (data.relation) {
        $ctrl.relation = angular.copy(data.relation);
        $ctrl.relation.agent = data.relation.agent.id;
        $ctrl.relation.type = data.relation.type.id;
      } else {
        $ctrl.relation = $ctrl.relationTemplate;
      }
      return $http({
        url: appConfig.djangoUrl + 'agents/',
        method: 'OPTIONS',
      }).then(function(response) {
        $ctrl.options.type = response.data.actions.POST.related_agents.child.children.type;
        $ctrl.loadForm();
        EditMode.enable();
        return response.data;
      });
    };

    $ctrl.loadForm = function() {
      $ctrl.fields = [
        {
          type: 'uiselect',
          key: 'agent',
          templateOptions: {
            required: true,
            options: function() {
              return $ctrl.options.agents;
            },
            valueProp: 'id',
            labelProp: 'full_name',
            placeholder: $translate.instant('ACCESS.ARCHIVE_CREATOR'),
            label: $translate.instant('ACCESS.ARCHIVE_CREATOR'),
            appendToBody: false,
            refresh: function(search) {
              $ctrl.getAgents(search).then(function() {
                this.options = $ctrl.options.agents;
              });
            },
          },
        },
        {
          type: 'select',
          key: 'type',
          templateOptions: {
            label: $translate.instant('TYPE'),
            options: $ctrl.options.type.choices,
            required: true,
            labelProp: 'display_name',
            valueProp: 'value',
            defaultValue: $ctrl.options.type.choices.length > 0 ? $ctrl.options.type.choices[0].value : null,
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
          key: 'description',
          type: 'textarea',
          templateOptions: {
            label: $translate.instant('DESCRIPTION'),
            rows: 3,
          }
        }
      ];
    };

    $ctrl.add = function() {
      if ($ctrl.form.$invalid) {
        $ctrl.form.$setSubmitted();
        return
      }
      $ctrl.adding = true;
      var related_agents = angular.copy($ctrl.agent.related_agents);
      related_agents.forEach(function(x, idx, array) {
        if (typeof x.type === 'object') {
          x.type = x.type.id;
        }
        if (typeof x.agent === 'object') {
          x.agent = x.agent.id;
        }
      });
      $http({
        url: appConfig.djangoUrl + 'agents/' + $ctrl.agent.id + '/',
        method: 'PATCH',
        data: {
          related_agents: related_agents.concat([$ctrl.relation]),
        },
      })
        .then(function(response) {
          $ctrl.adding = false;
          EditMode.disable();
          $uibModalInstance.close(response.data);
        })
        .catch(function() {
          $ctrl.adding = false;
          EditMode.disable();
        });
    };

    $ctrl.save = function() {
      if ($ctrl.form.$invalid) {
        $ctrl.form.$setSubmitted();
        return
      }
      $ctrl.saving = true;
      var related_agents = angular.copy($ctrl.agent.related_agents);
      related_agents.forEach(function(x, idx, array) {
        if (typeof x.type === 'object') {
          x.type = x.type.id;
        }
        if (typeof x.agent === 'object') {
          x.agent = x.agent.id;
        }
        if (x.id === $ctrl.relation.id) {
          array[idx] = $ctrl.relation;
        }
      });
      $http({
        url: appConfig.djangoUrl + 'agents/' + $ctrl.agent.id + '/',
        method: 'PATCH',
        data: {
          related_agents: related_agents,
        },
      })
        .then(function(response) {
          $ctrl.saving = false;
          EditMode.disable();
          $uibModalInstance.close(response.data);
        })
        .catch(function() {
          $ctrl.saving = false;
          EditMode.disable();
        });
    };

    $ctrl.remove = function() {
      $ctrl.removing = true;
      var related_agents = angular.copy($ctrl.agent.related_agents);
      related_agents.forEach(function(x, idx, array) {
        if (typeof x.type === 'object') {
          x.type = x.type.id;
        }
        if (typeof x.agent === 'object') {
          x.agent = x.agent.id;
        }
        if (x.id === $ctrl.relation.id) {
          array.splice(idx, 1);
        }
      });
      $http({
        url: appConfig.djangoUrl + 'agents/' + $ctrl.agent.id + '/',
        method: 'PATCH',
        data: {
          related_agents: related_agents,
        },
      })
        .then(function(response) {
          $ctrl.removing = false;
          EditMode.disable();
          $uibModalInstance.close(response.data);
        })
        .catch(function() {
          $ctrl.removing = false;
          EditMode.disable();
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
