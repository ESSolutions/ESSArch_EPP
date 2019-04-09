angular
  .module('essarch.controllers')
  .controller('AgentCtrl', function(
    $uibModal,
    $log,
    $scope,
    $http,
    appConfig,
    $state,
    $stateParams,
    EditMode,
    AgentName
  ) {
    var vm = this;
    $scope.AgentName = AgentName;
    $scope.$state = $state;
    vm.agentsLoading = false;
    vm.agents = [];
    vm.agent = null;
    vm.accordion = {
      basic: {
        basic: {
          open: true,
        },
        identifiers: {
          open: true,
        },
        names: {
          open: true,
        },
        mandates: {
          open: true,
        },
        authority: {
          open: true,
        },
        resources: {
          open: true,
        },
      },
      history: {
        open: true,
      },
      remarks: {
        notes: {
          open: true,
        },
        places: {
          open: true,
        },
      },
      topography: {
        open: true,
      },
    };

    vm.getAgent = function(agent) {
      $http.get(appConfig.djangoUrl + 'agents/' + agent.id + '/').then(function(response) {
        vm.initAccordion();
        vm.sortNotes(response.data);
        vm.sortNames(response.data);
        AgentName.parseAgentNames(response.data);
        response.data.auth_name = AgentName.getAuthorizedName(response.data);
        vm.agent = response.data;
      });
    };

    vm.$onInit = function() {
      if ($stateParams.id) {
        vm.getAgent($stateParams);
      } else {
        vm.agent = null;
      }
    };

    vm.initAccordion = function() {
      angular.forEach(vm.accordion, function(value) {
        value.open = true;
      });
    };

    vm.agentClick = function(agent) {
      if (vm.agent === null || (vm.agent !== null && agent.id !== vm.agent.id)) {
        $http.get(appConfig.djangoUrl + 'agents/' + agent.id + '/').then(function(response) {
          vm.agent = response.data;
          vm.initAccordion();
          vm.sortNotes(agent);
          vm.agent = agent;
          vm.agentArchivePipe($scope.archiveTableState);
          vm.sortNames(vm.agent);
          $state.go($state.current.name, vm.agent, {notify: false});
        });
      } else if (vm.agent !== null && vm.agent.id === agent.id) {
        vm.agent = null;
        $state.go($state.current.name, {id: null}, {notify: false});
      }
    };

    vm.sortNames = function(agent) {
      agent.names.sort(function(a, b) {
        return new Date(b.start_date) - new Date(a.start_date);
      });
      agent.names.forEach(function(x, index) {
        if (x.type.name.toLowerCase() === 'auktoriserad') {
          var name = x;
          agent.names.splice(index, 1);
          agent.names.unshift(name);
        }
      });
    };

    vm.archiveClick = function(agentArchive) {
      $state.go('home.access.search.archive', {id: agentArchive.archive._id});
    };

    vm.agentPipe = function(tableState) {
      vm.agentsLoading = true;
      if (vm.agents.length == 0) {
        $scope.initLoad = true;
      }
      if (!angular.isUndefined(tableState)) {
        $scope.tableState = tableState;
        var search = '';
        if (tableState.search.predicateObject) {
          var search = tableState.search.predicateObject['$'];
        }
        var sorting = tableState.sort;
        var pagination = tableState.pagination;
        var start = pagination.start || 0; // This is NOT the page number, but the index of item in the list that you want to use to display the table.
        var number = pagination.number || vm.agentsPerPage; // Number of entries showed per page.
        var pageNumber = start / number + 1;

        var sortString = sorting.predicate;
        if (sorting.reverse) {
          sortString = '-' + sortString;
        }

        vm.getAgents({
          page: pageNumber,
          page_size: number,
          ordering: sortString,
          search: search,
        }).then(function(response) {
          tableState.pagination.numberOfPages = Math.ceil(response.headers('Count') / number); //set the number of pages so the pagination can update
          $scope.initLoad = false;
          vm.agentsLoading = false;
          vm.parseAgents(response.data);
          vm.agents = response.data;
        });
      }
    };

    vm.getAgents = function(params) {
      return $http({
        url: appConfig.djangoUrl + 'agents/',
        method: 'GET',
        params: params,
      }).then(function(response) {
        return response;
      });
    };

    vm.parseAgents = function(list) {
      list.forEach(function(agent) {
        AgentName.parseAgentNames(agent);
        agent.auth_name = AgentName.getAuthorizedName(agent, {includeDates: false});
      });
    };

    vm.agentArchivePipe = function(tableState) {
      vm.archivesLoading = true;
      if (angular.isUndefined(vm.agent.archives) || vm.agent.archives.length == 0) {
        $scope.initLoad = true;
      }
      if (!angular.isUndefined(tableState)) {
        $scope.archiveTableState = tableState;
        var search = '';
        if (tableState.search.predicateObject) {
          var search = tableState.search.predicateObject['$'];
        }
        var sorting = tableState.sort;
        var pagination = tableState.pagination;
        var start = pagination.start || 0; // This is NOT the page number, but the index of item in the list that you want to use to display the table.
        var number = pagination.number || vm.agentsPerPage; // Number of entries showed per page.
        var pageNumber = start / number + 1;

        var sortString = sorting.predicate;
        if (sorting.reverse) {
          sortString = '-' + sortString;
        }

        vm.getAgentArchives(vm.agent, {
          page: pageNumber,
          page_size: number,
          ordering: sortString,
          search: search,
        }).then(function(response) {
          tableState.pagination.numberOfPages = Math.ceil(response.headers('Count') / number); //set the number of pages so the pagination can update
          $scope.initLoad = false;
          vm.archivesLoading = false;
          vm.agent.archives = response.data;
        });
      }
    };

    vm.getAgentArchives = function(agent, params) {
      return $http({
        url: appConfig.djangoUrl + 'agents/' + agent.id + '/archives/',
        method: 'GET',
        params: params,
      }).then(function(response) {
        return response;
      });
    };

    vm.sortNotes = function(agent) {
      var obj = {
        history: [],
        remarks: [],
      };
      agent.notes.forEach(function(note) {
        if (note.type.name.toLowerCase() === 'historik') {
          obj.history.push(note);
        } else {
          obj.remarks.push(note);
        }
      });
      angular.extend(agent, obj);
    };

    vm.createModal = function() {
      var modalInstance = $uibModal.open({
        animation: true,
        ariaLabelledBy: 'modal-title',
        ariaDescribedBy: 'modal-body',
        templateUrl: 'static/frontend/views/new_agent_modal.html',
        controller: 'AgentModalInstanceCtrl',
        controllerAs: '$ctrl',
        size: 'lg',
        resolve: {
          data: function() {
            return {};
          },
        },
      });
      modalInstance.result.then(
        function(data) {
          $state.go($state.current.name, {id: data.id});
        },
        function() {
          $log.info('modal-component dismissed at: ' + new Date());
        }
      );
    };

    vm.editModal = function(agent) {
      var modalInstance = $uibModal.open({
        animation: true,
        ariaLabelledBy: 'modal-title',
        ariaDescribedBy: 'modal-body',
        templateUrl: 'static/frontend/views/edit_agent_modal.html',
        controller: 'AgentModalInstanceCtrl',
        controllerAs: '$ctrl',
        size: 'lg',
        resolve: {
          data: function() {
            return {
              agent: agent,
            };
          },
        },
      });
      modalInstance.result.then(
        function(data) {
          vm.agentPipe($scope.tableState);
          if (vm.agent) {
            vm.getAgent(vm.agent);
          }
        },
        function() {
          $log.info('modal-component dismissed at: ' + new Date());
        }
      );
    };

    vm.removeAgentModal = function(agent) {
      var modalInstance = $uibModal.open({
        animation: true,
        ariaLabelledBy: 'modal-title',
        ariaDescribedBy: 'modal-body',
        templateUrl: 'static/frontend/views/remove_agent_modal.html',
        controller: 'AgentModalInstanceCtrl',
        controllerAs: '$ctrl',
        size: 'lg',
        resolve: {
          data: function() {
            return {
              agent: agent,
              allow_close: true,
            };
          },
        },
      });
      modalInstance.result.then(
        function(data) {
          vm.agent = null;
          $state.go($state.current.name, {id: null}, {notify: false});
          vm.agentPipe($scope.tableState);
        },
        function() {
          $log.info('modal-component dismissed at: ' + new Date());
        }
      );
    };
    vm.addNoteModal = function() {
      var modalInstance = $uibModal.open({
        animation: true,
        ariaLabelledBy: 'modal-title',
        ariaDescribedBy: 'modal-body',
        templateUrl: 'static/frontend/views/add_agent_note_modal.html',
        controller: 'AgentNoteModalInstanceCtrl',
        controllerAs: '$ctrl',
        size: 'lg',
        resolve: {
          data: function() {
            return {
              agent: vm.agent,
            };
          },
        },
      });
      modalInstance.result.then(
        function(data) {
          vm.getAgent(vm.agent);
        },
        function() {
          $log.info('modal-component dismissed at: ' + new Date());
        }
      );
    };

    vm.editNoteModal = function(note) {
      var modalInstance = $uibModal.open({
        animation: true,
        ariaLabelledBy: 'modal-title',
        ariaDescribedBy: 'modal-body',
        templateUrl: 'static/frontend/views/edit_agent_note_modal.html',
        controller: 'AgentNoteModalInstanceCtrl',
        controllerAs: '$ctrl',
        size: 'lg',
        resolve: {
          data: function() {
            return {
              agent: vm.agent,
              note: note,
            };
          },
        },
      });
      modalInstance.result.then(
        function(data) {
          vm.getAgent(vm.agent);
        },
        function() {
          $log.info('modal-component dismissed at: ' + new Date());
        }
      );
    };

    vm.removeNoteModal = function(note) {
      var modalInstance = $uibModal.open({
        animation: true,
        ariaLabelledBy: 'modal-title',
        ariaDescribedBy: 'modal-body',
        templateUrl: 'static/frontend/views/remove_agent_note_modal.html',
        controller: 'AgentNoteModalInstanceCtrl',
        controllerAs: '$ctrl',
        size: 'lg',
        resolve: {
          data: function() {
            return {
              agent: vm.agent,
              note: note,
              allow_close: true,
            };
          },
        },
      });
      modalInstance.result.then(
        function(data) {
          vm.agentPipe($scope.tableState);
          vm.getAgent(vm.agent);
        },
        function() {
          $log.info('modal-component dismissed at: ' + new Date());
        }
      );
    };

    vm.addNameModal = function() {
      var modalInstance = $uibModal.open({
        animation: true,
        ariaLabelledBy: 'modal-title',
        ariaDescribedBy: 'modal-body',
        templateUrl: 'static/frontend/views/add_agent_name_modal.html',
        controller: 'AgentNameModalInstanceCtrl',
        controllerAs: '$ctrl',
        size: 'lg',
        resolve: {
          data: function() {
            return {
              agent: vm.agent,
            };
          },
        },
      });
      modalInstance.result.then(
        function(data) {
          vm.getAgent(vm.agent);
        },
        function() {
          $log.info('modal-component dismissed at: ' + new Date());
        }
      );
    };

    vm.editNameModal = function(name) {
      var modalInstance = $uibModal.open({
        animation: true,
        ariaLabelledBy: 'modal-title',
        ariaDescribedBy: 'modal-body',
        templateUrl: 'static/frontend/views/edit_agent_name_modal.html',
        controller: 'AgentNameModalInstanceCtrl',
        controllerAs: '$ctrl',
        size: 'lg',
        resolve: {
          data: function() {
            return {
              agent: vm.agent,
              name: name,
            };
          },
        },
      });
      modalInstance.result.then(
        function(data) {
          vm.getAgent(vm.agent);
        },
        function() {
          $log.info('modal-component dismissed at: ' + new Date());
        }
      );
    };

    vm.removeNameModal = function(name) {
      var modalInstance = $uibModal.open({
        animation: true,
        ariaLabelledBy: 'modal-title',
        ariaDescribedBy: 'modal-body',
        templateUrl: 'static/frontend/views/remove_agent_name_modal.html',
        controller: 'AgentNameModalInstanceCtrl',
        controllerAs: '$ctrl',
        size: 'lg',
        resolve: {
          data: function() {
            return {
              agent: vm.agent,
              name: name,
              allow_close: true,
            };
          },
        },
      });
      modalInstance.result.then(
        function(data) {
          vm.agentPipe($scope.tableState);
          vm.getAgent(vm.agent);
        },
        function() {
          $log.info('modal-component dismissed at: ' + new Date());
        }
      );
    };

    vm.addMandateModal = function() {
      var modalInstance = $uibModal.open({
        animation: true,
        ariaLabelledBy: 'modal-title',
        ariaDescribedBy: 'modal-body',
        templateUrl: 'static/frontend/views/add_agent_mandate_modal.html',
        controller: 'AgentMandateModalInstanceCtrl',
        controllerAs: '$ctrl',
        size: 'lg',
        resolve: {
          data: function() {
            return {
              agent: vm.agent,
            };
          },
        },
      });
      modalInstance.result.then(
        function(data) {
          vm.getAgent(vm.agent);
        },
        function() {
          $log.info('modal-component dismissed at: ' + new Date());
        }
      );
    };

    vm.editMandateModal = function(mandate) {
      var modalInstance = $uibModal.open({
        animation: true,
        ariaLabelledBy: 'modal-title',
        ariaDescribedBy: 'modal-body',
        templateUrl: 'static/frontend/views/edit_agent_mandate_modal.html',
        controller: 'AgentMandateModalInstanceCtrl',
        controllerAs: '$ctrl',
        size: 'lg',
        resolve: {
          data: function() {
            return {
              agent: vm.agent,
              mandate: mandate,
            };
          },
        },
      });
      modalInstance.result.then(
        function(data) {
          vm.getAgent(vm.agent);
        },
        function() {
          $log.info('modal-component dismissed at: ' + new Date());
        }
      );
    };

    vm.removeMandateModal = function(mandate) {
      var modalInstance = $uibModal.open({
        animation: true,
        ariaLabelledBy: 'modal-title',
        ariaDescribedBy: 'modal-body',
        templateUrl: 'static/frontend/views/remove_agent_mandate_modal.html',
        controller: 'AgentMandateModalInstanceCtrl',
        controllerAs: '$ctrl',
        size: 'lg',
        resolve: {
          data: function() {
            return {
              agent: vm.agent,
              mandate: mandate,
              allow_close: true,
            };
          },
        },
      });
      modalInstance.result.then(
        function(data) {
          vm.agentPipe($scope.tableState);
          vm.getAgent(vm.agent);
        },
        function() {
          $log.info('modal-component dismissed at: ' + new Date());
        }
      );
    };

    vm.addAgentRelationModal = function() {
      var modalInstance = $uibModal.open({
        animation: true,
        ariaLabelledBy: 'modal-title',
        ariaDescribedBy: 'modal-body',
        templateUrl: 'static/frontend/views/add_agent_relation_modal.html',
        controller: 'AgentRelationModalInstanceCtrl',
        controllerAs: '$ctrl',
        size: 'lg',
        resolve: {
          data: function() {
            return {
              agent: vm.agent,
            };
          },
        },
      });
      modalInstance.result.then(
        function(data) {
          vm.agentPipe($scope.tableState);
          vm.getAgent(vm.agent);
        },
        function() {
          $log.info('modal-component dismissed at: ' + new Date());
        }
      );
    };

    vm.editAgentRelationModal = function(relation) {
      var modalInstance = $uibModal.open({
        animation: true,
        ariaLabelledBy: 'modal-title',
        ariaDescribedBy: 'modal-body',
        templateUrl: 'static/frontend/views/edit_agent_relation_modal.html',
        controller: 'AgentRelationModalInstanceCtrl',
        controllerAs: '$ctrl',
        size: 'lg',
        resolve: {
          data: function() {
            return {
              agent: vm.agent,
              relation: relation,
            };
          },
        },
      });
      modalInstance.result.then(
        function(data) {
          vm.agentPipe($scope.tableState);
          vm.getAgent(vm.agent);
        },
        function() {
          $log.info('modal-component dismissed at: ' + new Date());
        }
      );
    };

    vm.removeAgentRelationModal = function(relation) {
      var modalInstance = $uibModal.open({
        animation: true,
        ariaLabelledBy: 'modal-title',
        ariaDescribedBy: 'modal-body',
        templateUrl: 'static/frontend/views/remove_agent_relation_modal.html',
        controller: 'AgentRelationModalInstanceCtrl',
        controllerAs: '$ctrl',
        size: 'lg',
        resolve: {
          data: function() {
            return {
              agent: vm.agent,
              relation: relation,
              allow_close: true,
            };
          },
        },
      });
      modalInstance.result.then(
        function(data) {
          vm.agentPipe($scope.tableState);
          vm.getAgent(vm.agent);
        },
        function() {
          $log.info('modal-component dismissed at: ' + new Date());
        }
      );
    };

    vm.addArchiveRelationModal = function() {
      var modalInstance = $uibModal.open({
        animation: true,
        ariaLabelledBy: 'modal-title',
        ariaDescribedBy: 'modal-body',
        templateUrl: 'static/frontend/views/add_agent_archive_relation_modal.html',
        controller: 'AgentArchiveRelationModalInstanceCtrl',
        controllerAs: '$ctrl',
        size: 'lg',
        resolve: {
          data: function() {
            return {
              agent: vm.agent,
            };
          },
        },
      });
      modalInstance.result.then(
        function(data) {
          vm.getAgent(vm.agent);
          vm.agentArchivePipe($scope.archiveTableState);
        },
        function() {
          $log.info('modal-component dismissed at: ' + new Date());
        }
      );
    };

    vm.editArchiveRelationModal = function(relation) {
      var modalInstance = $uibModal.open({
        animation: true,
        ariaLabelledBy: 'modal-title',
        ariaDescribedBy: 'modal-body',
        templateUrl: 'static/frontend/views/edit_agent_archive_relation_modal.html',
        controller: 'AgentArchiveRelationModalInstanceCtrl',
        controllerAs: '$ctrl',
        size: 'lg',
        resolve: {
          data: function() {
            return {
              agent: vm.agent,
              relation: relation,
            };
          },
        },
      });
      modalInstance.result.then(
        function(data) {
          vm.getAgent(vm.agent);
          vm.agentArchivePipe($scope.archiveTableState);
        },
        function() {
          $log.info('modal-component dismissed at: ' + new Date());
        }
      );
    };

    vm.removeArchiveRelationModal = function(relation) {
      var modalInstance = $uibModal.open({
        animation: true,
        ariaLabelledBy: 'modal-title',
        ariaDescribedBy: 'modal-body',
        templateUrl: 'static/frontend/views/remove_agent_archive_relation_modal.html',
        controller: 'AgentArchiveRelationModalInstanceCtrl',
        controllerAs: '$ctrl',
        size: 'lg',
        resolve: {
          data: function() {
            return {
              agent: vm.agent,
              relation: relation,
              allow_close: true,
            };
          },
        },
      });
      modalInstance.result.then(
        function(data) {
          vm.getAgent(vm.agent);
          vm.agentArchivePipe($scope.archiveTableState);
        },
        function() {
          $log.info('modal-component dismissed at: ' + new Date());
        }
      );
    };
  });
