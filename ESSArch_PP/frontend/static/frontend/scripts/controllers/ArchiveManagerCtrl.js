angular
  .module('essarch.controllers')
  .controller('ArchiveManagerCtrl', function($scope, $http, appConfig, Search, Notifications, $translate) {
    var vm = this;
    vm.structure = null;
    vm.structures = [];
    vm.options = {agents: []};
    vm.$onInit = function() {
      $http({
        method: 'GET',
        url: appConfig.djangoUrl + 'classification-structures/',
      }).then(function(response) {
        vm.structures = response.data;
        if (vm.structures.length > 0) {
          vm.structure = vm.structures[0];
        }
      });
    };

    vm.getAuthorizedName = function(agent) {
      var name;
      agent.names.forEach(function(x) {
        x.full_name = (x.part !== null && x.part !== '' ? x.part + ', ' : '') + x.main;
        if (x.type.name.toLowerCase() === 'auktoriserad') {
          name = x;
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

    vm.createArchive = function(archiveName, structureName, type, referenceCode, archiveCreator, archiveResponsible) {
      Search.addNode({
        name: archiveName,
        structure: structureName,
        index: 'archive',
        type: type,
        reference_code: referenceCode,
        archive_creator: archiveCreator,
        archive_responsible: archiveResponsible,
      }).then(function(response) {
        vm.archiveName = null;
        vm.structure = null;
        vm.nodeType = null;
        vm.referenceCode = null;
        vm.archiveResponsible = null;
        vm.archiveCreator = null;
        Notifications.add($translate.instant('ACCESS.NEW_ARCHIVE_CREATED'), 'success');
      });
    };
  });
