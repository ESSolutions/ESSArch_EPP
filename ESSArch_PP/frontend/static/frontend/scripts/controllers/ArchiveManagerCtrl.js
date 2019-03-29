angular
  .module('essarch.controllers')
  .controller('ArchiveManagerCtrl', function($scope, $http, appConfig, Search, Notifications, $translate) {
    var vm = this;
    vm.structure = null;
    vm.archive = {};
    vm.fields = [];
    vm.$onInit = function() {
      vm.options = {agents: [], structures: [], type: []};
      vm.getStructures().then(function(structures) {
        if (structures.length > 0) {
          vm.structure = structures[0];
        }
        vm.getTypes().then(function(types) {
          vm.options.type = types;
          vm.buildForm();
        });
      });
    };

    vm.getTypes = function() {
      return $http.get(appConfig.djangoUrl + 'tag-version-types/', {params: {archive_type: true, pager: 'none'}}).then(function(response) {
        return angular.copy(response.data);
      });
    };

    vm.getAuthorizedName = function(agent) {
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

    vm.getAgents = function(search) {
      return $http({
        url: appConfig.djangoUrl + 'agents/',
        mathod: 'GET',
        params: {page: 1, page_size: 10, search: search},
      }).then(function(response) {
        response.data.forEach(function(agent) {
          agent.auth_name = vm.getAuthorizedName(agent);
        });
        vm.options.agents = response.data;
        return vm.options.agents;
      });
    };

    vm.getStructures = function(search) {
      return $http({
        url: appConfig.djangoUrl + 'structures/',
        mathod: 'GET',
        params: {page: 1, page_size: 10, search: search, template: true},
      }).then(function(response) {
        vm.options.structures = response.data;
        return vm.options.structures;
      });
    };

    vm.createArchive = function(archive) {
      if (vm.form.$invalid) {
        vm.form.$setSubmitted();
        return;
      }
      Search.addNode(
        angular.extend(archive, {
          index: 'archive',
        })
      ).then(function(response) {
        vm.archive = {};
        Notifications.add($translate.instant('ACCESS.NEW_ARCHIVE_CREATED'), 'success');
      });
    };

    vm.buildForm = function() {
      vm.fields = [
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
              return vm.options.structures;
            },
            valueProp: 'id',
            labelProp: 'name',
            placeholder: $translate.instant('ACCESS.CLASSIFICATION_STRUCTURE'),
            label: $translate.instant('ACCESS.CLASSIFICATION_STRUCTURE'),
            appendToBody: false,
            refresh: function(search) {
              vm.getStructures(search).then(function() {
                this.options = vm.options.structures;
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
              return vm.options.agents;
            },
            valueProp: 'id',
            labelProp: 'full_name',
            placeholder: $translate.instant('ACCESS.ARCHIVE_CREATOR'),
            label: $translate.instant('ACCESS.ARCHIVE_CREATOR'),
            appendToBody: false,
            refresh: function(search) {
              vm.getAgents(search).then(function() {
                this.options = vm.options.agents;
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
            options: vm.options.type,
            valueProp: 'pk',
            labelProp: 'name',
            required: true,
            label: $translate.instant('TYPE'),
            notNull: true,
          },
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
  });
