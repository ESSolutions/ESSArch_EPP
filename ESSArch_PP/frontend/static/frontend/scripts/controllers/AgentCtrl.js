angular
  .module('essarch.controllers')
  .controller('AgentCtrl', function($uibModal, $log, $scope, $http, appConfig, $state, $stateParams) {
    var vm = this;
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

    vm.$onInit = function() {
      if ($stateParams.id) {
        $http.get(appConfig.djangoUrl + 'agents/' + $stateParams.id + '/').then(function(response) {
          vm.initAccordion();
          vm.sortNotes(response.data);
          vm.sortNames(response.data);
          response.data.auth_name = vm.getAuthorizedName(response.data);

          vm.agent = response.data;
        });
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
        if (x.type.toLowerCase() === 'auktoriserad') {
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
        agent.auth_name = vm.getAuthorizedName(agent);
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
        if (note.type.toLowerCase() === 'historik') {
          obj.history.push(note);
        } else {
          obj.remarks.push(note);
        }
      });
      angular.extend(agent, obj);
    };

    vm.getAuthorizedName = function(agent) {
      var name;
      agent.names.forEach(function(x) {
        x.full_name = (x.part !== null && x.part !== '' ? x.part + ', ' : '') + x.main;
        if (x.type === 'auktoriserad') {
          name = x;
        }
      });
      return name;
    };

    vm.edit = function(row) {
      if (angular.isUndefined(row.edit)) {
        row.edit = angular.copy(row);
      }
    };

    vm.save = function(row) {
      var rowWithoutEdit = angular.copy(row);
      delete rowWithoutEdit.edit;
      var diff = {};
      angular.forEach(rowWithoutEdit, function(value, key) {
        if (!angular.equals(value, row.edit[key])) {
          diff[key] = row.edit[key];
        }
      });
      console.log(diff);
      delete row.edit;
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
        function(data) {},
        function() {
          $log.info('modal-component dismissed at: ' + new Date());
        }
      );
    };

    vm.editModal = function(creator) {
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
              creator: creator,
            };
          },
        },
      });
      modalInstance.result.then(
        function(data) {},
        function() {
          $log.info('modal-component dismissed at: ' + new Date());
        }
      );
    };
  });
