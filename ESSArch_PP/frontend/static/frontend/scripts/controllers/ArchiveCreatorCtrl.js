angular
  .module('essarch.controllers')
  .controller('ArchiveCreatorCtrl', function($timeout, $q, $uibModal, $log, $scope, $http, appConfig, IPTable) {
    var vm = this;
    vm.creatorsLoading = false;
    vm.creators = [];
    vm.creator = null;

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

    vm.initAccordion = function() {
      angular.forEach(vm.accordion, function(value) {
        value.open = true;
      });
    };

    vm.creatorClick = function(creator) {
      if (vm.creator === null || (vm.creator !== null && creator.id !== vm.creator.id)) {
        vm.initAccordion();
        vm.sortNotes(creator);
        vm.creator = creator;
      } else if (vm.creator !== null && vm.creator.id === creator.id) {
        vm.creator = null;
      }
    };

    vm.creatorPipe = function(tableState) {
      vm.creatorsLoading = true;
      if (vm.creators.length == 0) {
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
        var number = pagination.number || vm.structuresPerPage; // Number of entries showed per page.
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
          vm.creatorsLoading = false;
          vm.parseCreators(response.data);
          vm.creators = response.data;
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

    vm.parseCreators = function(list) {
      list.forEach(function(creator) {
        creator.auth_name = vm.getAuthorizedName(creator);
      });
    };

    vm.sortNotes = function(creator) {
      var obj = {
        history: [],
        remarks: [],
      };
      creator.notes.forEach(function(note) {
        if (note.type === 'historik') {
          obj.history.push(note);
        } else {
          obj.remarks.push(note);
        }
      });
      angular.extend(creator, obj);
    };

    vm.getAuthorizedName = function(creator) {
      var name;
      creator.names.forEach(function(x) {
        if (x.type === 'auktoriserad') {
          x.full_name = (x.part !== null && x.part !== '' ? x.part + ', ' : '') + x.main;
          name = x;
        }
      });
      return name;
    };

    vm.createModal = function() {
      var modalInstance = $uibModal.open({
        animation: true,
        ariaLabelledBy: 'modal-title',
        ariaDescribedBy: 'modal-body',
        templateUrl: 'static/frontend/views/new_archive_creator_modal.html',
        controller: 'ArchiveCreatorModalInstanceCtrl',
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
          list.push(data);
        },
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
        templateUrl: 'static/frontend/views/edit_archive_creator_modal.html',
        controller: 'ArchiveCreatorModalInstanceCtrl',
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
        function(data) {
          vm.creator = data;
        },
        function() {
          $log.info('modal-component dismissed at: ' + new Date());
        }
      );
    };
  });
