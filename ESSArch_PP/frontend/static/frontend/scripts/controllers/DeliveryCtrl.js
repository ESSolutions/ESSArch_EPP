angular.module('essarch.controllers').controller('DeliveryCtrl', [
  '$scope',
  'appConfig',
  '$http',
  '$q',
  '$timeout',
  '$uibModal',
  '$log',
  'listViewService',
  '$translate',
  function($scope, appConfig, $http, $q, $timeout, $uibModal, $log, listViewService, $translate) {
    var vm = this;
    $scope.$translate = $translate;
    vm.selected = null;
    vm.selectedTransfer = null;
    vm.deliveries = [];
    vm.transfers = [];
    vm.types = [];
    vm.tags = [];
    vm.units = [];

    vm.$onInit = function() {
      vm.initLoad = true;
      listViewService.getEventlogData().then(function(types) {
        vm.types = types;
        vm.initLoad = false;
      });
    };

    vm.mapEventType = function(type) {
      var mapped = type;
      vm.types.forEach(function(x) {
        if (x.eventType === type) {
          mapped = x.eventDetail;
        }
      });
      return mapped;
    };

    vm.deliveryClick = function(delivery) {
      if (vm.selected !== null && delivery.id === vm.selected.id) {
        vm.selected = null;
      } else {
        vm.selected = null;
        $timeout(function() {
          vm.selected = delivery;
          vm.tagsPipe(vm.tagsTableState);
          vm.unitsPipe(vm.unitsTableState);
        })
      }
    };

    vm.transferClick = function(transfer) {
      if (vm.selectedTransfer !== null && transfer.id === vm.selectedTransfer.id) {
        vm.selectedTransfer = null;
      } else {
        vm.selectedTransfer = transfer;
      }
    };

    vm.deliveryPipe = function(tableState) {
      if (vm.deliveries.length == 0) {
        $scope.initLoad = true;
      }
      vm.deliveriesLoading = true;
      if (!angular.isUndefined(tableState)) {
        vm.tableState = tableState;
        var search = '';
        if (tableState.search.predicateObject) {
          var search = tableState.search.predicateObject['$'];
        }
        var sorting = tableState.sort;
        var pagination = tableState.pagination;
        var start = pagination.start || 0; // This is NOT the page number, but the index of item in the list that you want to use to display the table.
        var number = pagination.number || vm.itemsPerPage || 10; // Number of entries showed per page.
        var pageNumber = start / number + 1;

        var sortString = sorting.predicate;
        if (sorting.reverse) {
          sortString = '-' + sortString;
        }

        vm.getDeliveries({
          page: pageNumber,
          page_size: number,
          ordering: sortString,
          search: search,
        }).then(function(response) {
          tableState.pagination.numberOfPages = Math.ceil(response.headers('Count') / number); //set the number of pages so the pagination can update
          $scope.initLoad = false;
          vm.deliveriesLoading = false;
          vm.deliveries = response.data;
        });
      }
    };

    vm.getDeliveries = function(params) {
      return $http.get(appConfig.djangoUrl + 'deliveries/', {params: params}).then(function(response) {
        return response;
      });
    };

    vm.transferPipe = function(tableState) {
      if (vm.transfers.length == 0) {
        $scope.initLoad = true;
      }
      vm.transfersLoading = true;
      if (!angular.isUndefined(tableState)) {
        vm.transferTableState = tableState;
        var search = '';
        if (tableState.search.predicateObject) {
          var search = tableState.search.predicateObject['$'];
        }
        var sorting = tableState.sort;
        var pagination = tableState.pagination;
        var start = pagination.start || 0; // This is NOT the page number, but the index of item in the list that you want to use to display the table.
        var number = pagination.number || vm.itemsPerPage || 10; // Number of entries showed per page.
        var pageNumber = start / number + 1;

        var sortString = sorting.predicate;
        if (sorting.reverse) {
          sortString = '-' + sortString;
        }

        vm.getTransfers({
          page: pageNumber,
          page_size: number,
          ordering: sortString,
          search: search,
        }).then(function(response) {
          tableState.pagination.numberOfPages = Math.ceil(response.headers('Count') / number); //set the number of pages so the pagination can update
          $scope.initLoad = false;
          vm.transfersLoading = false;
          vm.transfers = response.data;
        });
      }
    };

    vm.getTransfers = function(params) {
      return $http
        .get(appConfig.djangoUrl + 'deliveries/' + vm.selected.id + '/transfers/', {params: params})
        .then(function(response) {
          return response;
        });
    };

    vm.tagsPipe = function(tableState) {
      vm.tagsLoading = true;
      if (angular.isUndefined(vm.tags) || vm.tags.length == 0) {
        $scope.initLoad = true;
      }
      if (!angular.isUndefined(tableState)) {
        vm.tagsTableState = tableState;
        var search = '';
        if (tableState.search.predicateObject) {
          var search = tableState.search.predicateObject['$'];
        }
        var sorting = tableState.sort;
        var pagination = tableState.pagination;
        var start = pagination.start || 0; // This is NOT the page number, but the index of item in the list that you want to use to display the table.
        var number = pagination.number || vm.itemsPerPage; // Number of entries showed per page.
        var pageNumber = start / number + 1;

        var sortString = sorting.predicate;
        if (sorting.reverse) {
          sortString = '-' + sortString;
        }

        vm.getTags(vm.selectedTransfer, {
          page: pageNumber,
          page_size: number,
          ordering: sortString,
          search: search,
        }).then(function(response) {
          tableState.pagination.numberOfPages = Math.ceil(response.headers('Count') / number); //set the number of pages so the pagination can update
          $scope.initLoad = false;
          vm.tagsLoading = false;
          vm.tags = response.data;
        });
      }
    };

    vm.getTags = function(transfer, params) {
      return $http
        .get(appConfig.djangoUrl + 'transfers/' + transfer.id + '/tags/', {params: params})
        .then(function(response) {
          return response;
        });
    };

    vm.unitsPipe = function(tableState) {
      vm.unitsLoading = true;
      if (angular.isUndefined(vm.units) || vm.units.length == 0) {
        $scope.initLoad = true;
      }
      if (!angular.isUndefined(tableState)) {
        vm.unitsTableState = tableState;
        var search = '';
        if (tableState.search.predicateObject) {
          var search = tableState.search.predicateObject['$'];
        }
        var sorting = tableState.sort;
        var pagination = tableState.pagination;
        var start = pagination.start || 0; // This is NOT the page number, but the index of item in the list that you want to use to display the table.
        var number = pagination.number || vm.itemsPerPage; // Number of entries showed per page.
        var pageNumber = start / number + 1;

        var sortString = sorting.predicate;
        if (sorting.reverse) {
          sortString = '-' + sortString;
        }

        vm.getUnits(vm.selectedTransfer, {
          page: pageNumber,
          page_size: number,
          ordering: sortString,
          search: search,
        }).then(function(response) {
          tableState.pagination.numberOfPages = Math.ceil(response.headers('Count') / number); //set the number of pages so the pagination can update
          $scope.initLoad = false;
          vm.unitsLoading = false;
          vm.units = response.data;
        });
      }
    };

    vm.getUnits = function(transfer, params) {
      return $http
        .get(appConfig.djangoUrl + 'transfers/' + transfer.id + '/structure-units/', {params: params})
        .then(function(response) {
          return response;
        });
    };

    vm.transferEventsPipe = function(tableState) {
      vm.transferEventsLoading = true;
      if (angular.isUndefined(vm.transferEvents) || vm.transferEvents.length == 0) {
        $scope.initLoad = true;
      }
      if (!angular.isUndefined(tableState)) {
        vm.transferEventsTableState = tableState;
        var search = '';
        if (tableState.search.predicateObject) {
          var search = tableState.search.predicateObject['$'];
        }
        var sorting = tableState.sort;
        var pagination = tableState.pagination;
        var start = pagination.start || 0; // This is NOT the page number, but the index of item in the list that you want to use to display the table.
        var number = pagination.number || vm.itemsPerPage; // Number of entries showed per page.
        var pageNumber = start / number + 1;

        var sortString = sorting.predicate;
        if (sorting.reverse) {
          sortString = '-' + sortString;
        }

        vm.getTransferEvents(vm.selectedTransfer, {
          page: pageNumber,
          page_size: number,
          ordering: sortString,
          search: search,
        }).then(function(response) {
          tableState.pagination.numberOfPages = Math.ceil(response.headers('Count') / number); //set the number of pages so the pagination can update
          $scope.initLoad = false;
          vm.transferEventsLoading = false;
          vm.transferEvents = response.data;
        });
      }
    };

    vm.getTransferEvents = function(transfer, params) {
      return $http
        .get(appConfig.djangoUrl + 'transfers/' + transfer.id + '/events/', {params: params})
        .then(function(response) {
          return response;
        });
    };

    vm.deliveryEventsPipe = function(tableState) {
      vm.deliveryEventsLoading = true;
      if (angular.isUndefined(vm.deliveryEvents) || vm.deliveryEvents.length == 0) {
        $scope.initLoad = true;
      }
      if (!angular.isUndefined(tableState)) {
        vm.deliveryEventsTableState = tableState;
        var search = '';
        if (tableState.search.predicateObject) {
          var search = tableState.search.predicateObject['$'];
        }
        var sorting = tableState.sort;
        var pagination = tableState.pagination;
        var start = pagination.start || 0; // This is NOT the page number, but the index of item in the list that you want to use to display the table.
        var number = pagination.number || vm.itemsPerPage; // Number of entries showed per page.
        var pageNumber = start / number + 1;

        var sortString = sorting.predicate;
        if (sorting.reverse) {
          sortString = '-' + sortString;
        }

        vm.getDeliveryEvents(vm.selected, {
          page: pageNumber,
          page_size: number,
          ordering: sortString,
          search: search,
        }).then(function(response) {
          tableState.pagination.numberOfPages = Math.ceil(response.headers('Count') / number); //set the number of pages so the pagination can update
          $scope.initLoad = false;
          vm.deliveryEventsLoading = false;
          vm.deliveryEvents = response.data;
        });
      }
    };

    vm.getDeliveryEvents = function(delivery, params) {
      return $http
        .get(appConfig.djangoUrl + 'deliveries/' + delivery.id + '/events/', {params: params})
        .then(function(response) {
          return response;
        });
    };

    vm.createModal = function() {
      var modalInstance = $uibModal.open({
        animation: true,
        ariaLabelledBy: 'modal-title',
        ariaDescribedBy: 'modal-body',
        templateUrl: 'static/frontend/views/new_delivery_modal.html',
        controller: 'DeliveryModalInstanceCtrl',
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
          vm.selected = data;
          vm.deliveryPipe(vm.tableState);
        },
        function() {
          $log.info('modal-component dismissed at: ' + new Date());
        }
      );
    };

    vm.editModal = function(delivery) {
      var modalInstance = $uibModal.open({
        animation: true,
        ariaLabelledBy: 'modal-title',
        ariaDescribedBy: 'modal-body',
        templateUrl: 'static/frontend/views/edit_delivery_modal.html',
        controller: 'DeliveryModalInstanceCtrl',
        controllerAs: '$ctrl',
        size: 'lg',
        resolve: {
          data: function() {
            return {
              delivery: delivery,
            };
          },
        },
      });
      modalInstance.result.then(
        function(data) {
          vm.deliveryPipe(vm.tableState);
        },
        function() {
          $log.info('modal-component dismissed at: ' + new Date());
        }
      );
    };

    vm.removeModal = function(delivery) {
      var modalInstance = $uibModal.open({
        animation: true,
        ariaLabelledBy: 'modal-title',
        ariaDescribedBy: 'modal-body',
        templateUrl: 'static/frontend/views/remove_delivery_modal.html',
        controller: 'DeliveryModalInstanceCtrl',
        controllerAs: '$ctrl',
        size: 'lg',
        resolve: {
          data: function() {
            return {
              delivery: delivery,
              allow_close: true,
              remove: true,
            };
          },
        },
      });
      modalInstance.result.then(
        function(data) {
          vm.selected = null;
          vm.deliveryPipe(vm.tableState);
        },
        function() {
          $log.info('modal-component dismissed at: ' + new Date());
        }
      );
    };

    // Transfers
    vm.createTransferModal = function() {
      var modalInstance = $uibModal.open({
        animation: true,
        ariaLabelledBy: 'modal-title',
        ariaDescribedBy: 'modal-body',
        templateUrl: 'static/frontend/views/new_transfer_modal.html',
        controller: 'TransferModalInstanceCtrl',
        controllerAs: '$ctrl',
        size: 'lg',
        resolve: {
          data: function() {
            return {
              delivery: vm.selected,
            };
          },
        },
      });
      modalInstance.result.then(
        function(data) {
          vm.selectedTransfer = data;
          vm.transferPipe(vm.transferTableState);
        },
        function() {
          $log.info('modal-component dismissed at: ' + new Date());
        }
      );
    };

    vm.editTransferModal = function(transfer) {
      var modalInstance = $uibModal.open({
        animation: true,
        ariaLabelledBy: 'modal-title',
        ariaDescribedBy: 'modal-body',
        templateUrl: 'static/frontend/views/edit_transfer_modal.html',
        controller: 'TransferModalInstanceCtrl',
        controllerAs: '$ctrl',
        size: 'lg',
        resolve: {
          data: function() {
            return {
              transfer: transfer,
            };
          },
        },
      });
      modalInstance.result.then(
        function(data) {
          vm.transferPipe(vm.transferTableState);
        },
        function() {
          $log.info('modal-component dismissed at: ' + new Date());
        }
      );
    };

    vm.removeTransferModal = function(transfer) {
      var modalInstance = $uibModal.open({
        animation: true,
        ariaLabelledBy: 'modal-title',
        ariaDescribedBy: 'modal-body',
        templateUrl: 'static/frontend/views/remove_transfer_modal.html',
        controller: 'TransferModalInstanceCtrl',
        controllerAs: '$ctrl',
        size: 'lg',
        resolve: {
          data: function() {
            return {
              transfer: transfer,
              allow_close: true,
              remove: true,
            };
          },
        },
      });
      modalInstance.result.then(
        function(data) {
          vm.selectedTransfer = null;
          vm.transferPipe(vm.transferTableState);
        },
        function() {
          $log.info('modal-component dismissed at: ' + new Date());
        }
      );
    };

    vm.createEventModal = function(params) {
      var data = {};
      if (params.transfer) {
        data.transfer = params.transfer;
      }
      if (params.delivery) {
        data.delivery = params.delivery;
      }
      var modalInstance = $uibModal.open({
        animation: true,
        ariaLabelledBy: 'modal-title',
        ariaDescribedBy: 'modal-body',
        templateUrl: 'static/frontend/views/new_event_modal.html',
        controller: 'EventModalInstanceCtrl',
        controllerAs: '$ctrl',
        size: 'lg',
        resolve: {
          data: function() {
            return data;
          },
        },
      });
      modalInstance.result.then(
        function(data) {
          if (params.transfer) {
            vm.transferPipe(vm.transferTableState);
            vm.transferEventsPipe(vm.transferEventsTableState);
          }
          if (params.delivery && !params.transfer) {
            vm.deliveryPipe(vm.tableState);
            vm.deliveryEventsPipe(vm.deliveryEventsTableState);
          }
        },
        function() {
          $log.info('modal-component dismissed at: ' + new Date());
        }
      );
    };

    vm.editEventModal = function(event, params) {
      var data = {
        event: event,
      };
      if (params.transfer) {
        data.transfer = params.transfer;
      }
      if (params.delivery) {
        data.delivery = params.delivery;
      }
      var modalInstance = $uibModal.open({
        animation: true,
        ariaLabelledBy: 'modal-title',
        ariaDescribedBy: 'modal-body',
        templateUrl: 'static/frontend/views/edit_event_modal.html',
        controller: 'EventModalInstanceCtrl',
        controllerAs: '$ctrl',
        size: 'lg',
        resolve: {
          data: function() {
            return data;
          },
        },
      });
      modalInstance.result.then(
        function(data) {
          if (vm.activeTab === 'events') {
            vm.deliveryPipe(vm.tableState);
            vm.deliveryEventsPipe(vm.deliveryEventsTableState);
          } else {
            vm.transferPipe(vm.transferTableState);
            vm.transferEventsPipe(vm.transferEventsTableState);
          }
        },
        function() {
          $log.info('modal-component dismissed at: ' + new Date());
        }
      );
    };

    vm.removeEventModal = function(event) {
      var modalInstance = $uibModal.open({
        animation: true,
        ariaLabelledBy: 'modal-title',
        ariaDescribedBy: 'modal-body',
        templateUrl: 'static/frontend/views/remove_event_modal.html',
        controller: 'EventModalInstanceCtrl',
        controllerAs: '$ctrl',
        size: 'lg',
        resolve: {
          data: function() {
            return {
              event: event
            };
          },
        },
      });
      modalInstance.result.then(
        function(data) {
          if (vm.activeTab === 'events') {
            vm.deliveryPipe(vm.tableState);
            vm.deliveryEventsPipe(vm.deliveryEventsTableState);
          } else {
            vm.transferPipe(vm.transferTableState);
            vm.transferEventsPipe(vm.transferEventsTableState);
          }
        },
        function() {
          $log.info('modal-component dismissed at: ' + new Date());
        }
      );
    };
  },
]);
