angular
  .module('essarch.controllers')
  .controller('ArchiveModalInstanceCtrl', function(
    Search,
    $translate,
    $uibModalInstance,
    appConfig,
    $http,
    data,
    Notifications,
    AgentName,
    EditMode,
    $scope,
    $rootScope,
    Utils,
    StructureName
  ) {
    var $ctrl = this;
    $ctrl.options = {};
    $ctrl.initStructureSearch = null;
    $ctrl.initAgentSearch = null;
    $ctrl.$onInit = function() {
      EditMode.enable();
      if (data.archive && data.remove) {
        $ctrl.archive = angular.copy(data.archive);
      } else {
        if (data.archive) {
          $ctrl.archive = angular.copy(data.archive);
          $ctrl.archive.type = angular.copy(data.archive.type.pk);
          $ctrl.initStructureSearch = angular.copy(data.archive.structures[0].name);
          $ctrl.initAgentSearch = angular.copy(data.archive.agents[0].agent.names[0].main);
          delete $ctrl.archive.identifiers;
          delete $ctrl.archive.notes;
          delete $ctrl.archive._source;
        } else {
          $ctrl.archive = {};
        }
        $ctrl.options = {agents: [], structures: [], type: []};
        $ctrl.getStructures().then(function(structures) {
          if ($ctrl.archive.structures) {
            var toAdd = [];
            StructureName.parseStructureNames($ctrl.archive.structures);
            $ctrl.archive.structures.forEach(function(b) {
              var exists = false;
              structures.forEach(function(a) {
                if (a.id === b.id) {
              a = angular.copy(b);
                  a.disabled = true;
                  exists = true;
                }
              });
              if (!exists) {
                toAdd.push(b);
              }
            });
            toAdd.forEach(function(x) {
              x.disabled = true;
              structures.push(x);
            })
            $ctrl.options.structures = structures;
            $ctrl.archive.structures = angular.copy($ctrl.archive.structures).map(function(x) {
              return x.id;
            });
          }
          $ctrl.getTypes().then(function(types) {
            $ctrl.options.type = types;
            $ctrl.buildForm();
          });
        });
      }
    };
    $ctrl.creating = false;

    $ctrl.getTypes = function() {
      return $http
        .get(appConfig.djangoUrl + 'tag-version-types/', {params: {archive_type: true, pager: 'none'}})
        .then(function(response) {
          return angular.copy(response.data);
        });
    };

    $ctrl.getAgents = function(search) {
      return $http({
        url: appConfig.djangoUrl + 'agents/',
        mathod: 'GET',
        params: {page: 1, page_size: 10, search: search},
      }).then(function(response) {
        response.data.forEach(function(agent) {
          AgentName.parseAgentNames(agent);
        });
        $ctrl.options.agents = response.data;
        return $ctrl.options.agents;
      });
    };

    $ctrl.getStructures = function(search) {
      return $http({
        url: appConfig.djangoUrl + 'structures/',
        mathod: 'GET',
        params: {page: 1, page_size: 10, search: search, is_template: true, published: true},
      }).then(function(response) {
        StructureName.parseStructureNames(response.data);
        $ctrl.options.structures = response.data;
        return $ctrl.options.structures;
      });
    };

    $ctrl.buildForm = function() {
      $ctrl.fields = [
        {
          type: 'input',
          key: 'name',
          templateOptions: {
            label: $translate.instant('NAME'),
            required: true,
          },
        },
      ];
      $ctrl.fields = $ctrl.fields.concat([
        {
          type: 'uiselect',
          key: 'structures',
          templateOptions: {
            required: true,
            options: function() {
              return $ctrl.options.structures;
            },
            valueProp: 'id',
            labelProp: 'name_with_version',
            multiple: true,
            placeholder: $translate.instant('ACCESS.CLASSIFICATION_STRUCTURES'),
            label: $translate.instant('ACCESS.CLASSIFICATION_STRUCTURES'),
            appendToBody: false,
            refresh: function(search) {
              if ($ctrl.initStructureSearch && (angular.isUndefined(search) || search === null || search === '')) {
                search = angular.copy($ctrl.initStructureSearch);
                $ctrl.initStructureSearch = null;
              }
              $ctrl.getStructures(search).then(function() {
                this.options = $ctrl.options.structures;
              });
            },
          },
        },
      ]);
      if (angular.isUndefined(data.archive) || data.archive === null) {
        $ctrl.fields = $ctrl.fields.concat([
          {
            type: 'uiselect',
            key: 'archive_creator',
            templateOptions: {
              required: true,
              options: function() {
                return $ctrl.options.agents;
              },
              valueProp: 'id',
              labelProp: 'full_name',
              multiple: false,
              placeholder: $translate.instant('ACCESS.ARCHIVE_CREATOR'),
              label: $translate.instant('ACCESS.ARCHIVE_CREATOR'),
              appendToBody: false,
              refresh: function(search) {
                if ($ctrl.initAgentSearch && (angular.isUndefined(search) || search === null || search === '')) {
                  search = angular.copy($ctrl.initAgentSearch);
                  $ctrl.initAgentSearch = null;
                }
                $ctrl.getAgents(search).then(function() {
                  this.options = $ctrl.options.agents;
                });
              },
            },
          },
        ]);
      }
      $ctrl.fields = $ctrl.fields.concat([
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
              },
            },
            {
              className: 'col-xs-12 col-sm-6 px-0 pl-md-base',
              type: 'datepicker',
              key: 'end_date',
              templateOptions: {
                label: $translate.instant('END_DATE'),
                appendToBody: false,
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
          },
        },
        {
          key: 'type',
          type: 'select',
          templateOptions: {
            options: $ctrl.options.type,
            valueProp: 'pk',
            labelProp: 'name',
            required: true,
            label: $translate.instant('TYPE'),
            notNull: true,
          },
          defaultValue: $ctrl.options.type.length > 0 ? $ctrl.options.type[0].pk : null,
        },
        {
          key: 'reference_code',
          type: 'input',
          templateOptions: {
            required: true,
            label: $translate.instant('ACCESS.REFERENCE_CODE'),
          },
        },
      ]);
    };

    $ctrl.create = function(archive) {
      if ($ctrl.form.$invalid) {
        $ctrl.form.$setSubmitted();
        return;
      }
      $ctrl.creating = true;
      $rootScope.skipErrorNotification = true;
      Search.addNode(
        angular.extend(archive, {
          index: 'archive',
        })
      )
        .then(function(response) {
          $ctrl.creating = false;
          Notifications.add($translate.instant('ACCESS.NEW_ARCHIVE_CREATED'), 'success');
          EditMode.disable();
          $uibModalInstance.close({archive: response.data});
        })
        .catch(function(response) {
          $ctrl.nonFieldErrors = response.data.non_field_errors;
          $ctrl.creating = false;
        });
    };

    $ctrl.save = function(archive) {
      if ($ctrl.form.$invalid) {
        $ctrl.form.$setSubmitted();
        return;
      }
      $ctrl.saving = true;
      var extraDiff = {}
      if(data.archive && data.archive.structures && (data.archive.structures.length !== $ctrl.archive.structures.length)) {
        extraDiff.structures = $ctrl.archive.structures;
      }
      Search.updateNode({_id: data.archive._id}, angular.extend(Utils.getDiff(data.archive, $ctrl.archive), extraDiff))
        .then(function(response) {
          $ctrl.saving = false;
          Notifications.add($translate.instant('ACCESS.ARCHIVE_SAVED'), 'success');
          EditMode.disable();
          $uibModalInstance.close({archive: response.data});
        })
        .catch(function(response) {
          $ctrl.nonFieldErrors = response.data.non_field_errors;
          $ctrl.saving = false;
        });
    };

    $ctrl.remove = function() {
      $ctrl.removing = true;
      $rootScope.skipErrorNotification = true;
      Search.removeNode({_id: data.archive.id})
        .then(function(response) {
          $ctrl.removing = false;
          EditMode.disable();
          $uibModalInstance.close('removed');
        })
        .catch(function(response) {
          $ctrl.nonFieldErrors = response.data.non_field_errors;
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
