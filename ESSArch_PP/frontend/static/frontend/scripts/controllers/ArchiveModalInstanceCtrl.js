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
    AgentName
  ) {
    var $ctrl = this;
    $ctrl.options = {};
    $ctrl.$onInit = function() {
      if (data.archive) {
        $ctrl.archive = data.archive;
      } else {
        $ctrl.archive = {};
      }
      $ctrl.options = {agents: [], structures: [], type: []};
      $ctrl.getStructures().then(function(structures) {
        if (structures.length > 0) {
          $ctrl.structure = structures[0];
        }
        $ctrl.getTypes().then(function(types) {
          $ctrl.options.type = types;
          $ctrl.buildForm();
        });
      });
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
        params: {page: 1, page_size: 10, search: search, is_template: true},
      }).then(function(response) {
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
        {
          type: 'uiselect',
          key: 'structure',
          templateOptions: {
            required: true,
            options: function() {
              return $ctrl.options.structures;
            },
            valueProp: 'id',
            labelProp: 'name',
            placeholder: $translate.instant('ACCESS.CLASSIFICATION_STRUCTURE'),
            label: $translate.instant('ACCESS.CLASSIFICATION_STRUCTURE'),
            appendToBody: false,
            refresh: function(search) {
              $ctrl.getStructures(search).then(function() {
                this.options = $ctrl.options.structures;
              });
            },
          },
        },
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
          className: 'row m-0',
          fieldGroup: [
            {
              className: 'col-xs-12 col-sm-6 px-0 pr-md-base',
              type: 'datepicker',
              key: 'start_date',
              templateOptions: {
                label: $translate.instant('START_DATE'),
                appendToBody: true,
              },
            },
            {
              className: 'col-xs-12 col-sm-6 px-0 pl-md-base',
              type: 'datepicker',
              key: 'end_date',
              templateOptions: {
                label: $translate.instant('END_DATE'),
                appendToBody: true,
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
      ];
    };

    $ctrl.create = function(archive) {
      if ($ctrl.form.$invalid) {
        $ctrl.form.$setSubmitted();
        return;
      }
      $ctrl.creating = true;
      Search.addNode(
        angular.extend(archive, {
          index: 'archive',
        })
      )
        .then(function(response) {
          $ctrl.creating = false;
          Notifications.add($translate.instant('ACCESS.NEW_ARCHIVE_CREATED'), 'success');
          $uibModalInstance.close({archive: response.data});
        })
        .catch(function() {
          $ctrl.creating = false;
        });
    };
    $ctrl.cancel = function() {
      $uibModalInstance.dismiss('cancel');
    };
  });
