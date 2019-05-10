angular
  .module('essarch.controllers')
  .controller('LocationTreeCtrl', function($scope, $http, appConfig, $translate, $uibModal, $log) {
    var vm = this;
    $scope.$translate = $translate;
    vm.treeData = [];
    vm.tags = [];
    vm.$onInit = function() {
      if (angular.isUndefined(vm.selected) || vm.selected === null) {
        vm.selected = null;
      }
      vm.buildTree();
    };
    vm.treeChange = function() {};
    vm.dropNode = function() {};
    vm.applyModelChanges = function() {};

    vm.parseNode = function(node) {
      node.text = node.name + ' (' + node.level_type.name + ')';
      node.state = {opened: true};
      delete node.parent;
      if (node.children && node.children.length > 0) {
        node.children.forEach(function(x) {
          vm.parseNode(x);
        });
      }
    };

    function getBreadcrumbs(node) {
      var tree = vm.treeInstance.jstree(true);
      var start = tree.get_node(node.id);

      if (start === false) {
        return [];
      }
      return tree.get_path(start, false, true).map(function(id) {
        return angular.copy(tree.get_node(id).original);
      });
    }

    vm.ignoreChanges = false;
    vm.ignoreRecordChanges = false;
    vm.newNode = {};

    vm.applyRecordModelChanges = function() {
      return !vm.ignoreRecordChanges;
    };

    vm.buildTree = function() {
      return $http.get(appConfig.djangoUrl + 'locations/').then(function(response) {
        response.data.forEach(function(x) {
          x.type = 'top_level';
          vm.parseNode(x);
        });
        vm.recreateTree(response.data);
        return response.data;
      });
    };

    vm.getNode = function(node_id) {
      return $http.get(appConfig.djangoUrl + 'locations/' + node_id + '/').then(function(response) {
        return response.data;
      });
    };

    vm.recreateTree = function(tags) {
      vm.ignoreChanges = true;
      if (angular.equals(tags, vm.treeData)) {
        vm.treeConfig.version++;
      } else {
        vm.treeData = angular.copy(tags);
        vm.treeConfig.version++;
      }
    };

    vm.treeConfig = {
      core: {
        multiple: false,
        animation: 50,
        error: function(error) {
          $log.error('treeCtrl: error from js tree - ' + angular.toJson(error));
        },
        check_callback: true,
        worker: true,
      },
      types: {
        default: {
          icon: 'far fa-folder',
        },
        top_level: {
          icon: 'fas fa-warehouse',
        },
        plus: {
          icon: 'fas fa-plus',
        },
      },
      dnd: {
        is_draggable: function(nodes) {
          return true;
        },
      },
      contextmenu: {
        items: function(node, callback) {
          var edit = {
            label: $translate.instant('EDIT'),
            action: function edit() {
              vm.editNodeModal(node.original);
            },
          };
          var add = {
            label: $translate.instant('ADD'),
            action: function() {
              vm.addNodeModal(node.original);
            },
          };
          var remove = {
            label: $translate.instant('REMOVE'),
            action: function() {
              vm.removeNodeModal(node.original);
            },
          };
          var actions = {
            edit: edit,
            add: add,
            remove: remove,
          };
          if (vm.readOnly === true) {
            actions = {};
          }
          callback(actions);
          return actions;
        },
      },
      version: 1,
      plugins: ['types', 'contextmenu', 'dnd'],
    };

    vm.selectNode = function(jqobj, event) {
      var node = event.node;
      if (vm.selected === null || (vm.selected !== null && vm.selected.id !== node.original.id)) {
        if (!vm.readOnly) {
          vm.setSelected(node.original);
        } else {
          node.original.breadcrumbs = getBreadcrumbs(node.original);
          vm.selected = node.original;
          if (vm.onSelect) {
            vm.onSelect({node: vm.selected});
          }
        }
      }
    };

    vm.deselectNode = function(jqobj, event) {
      vm.selected = null;
    };

    vm.ready = function(jqobj, event) {
      if (vm.selected !== null && !angular.isUndefined(vm.selected)) {
        vm.setSelected(vm.selected).then(function() {
          vm.markTreeNode(vm.selected);
        });
      }
    };

    vm.setSelected = function(node) {
      return vm.getTags(node).then(function(response) {
        node.breadcrumbs = getBreadcrumbs(node);
        vm.selected = node;
        vm.tags = response.data;
        if (vm.onSelect) {
          vm.onSelect({node: vm.selected});
        }
        return response.data;
      });
    };

    vm.markTreeNode = function(node) {
      vm.treeInstance.jstree(true).deselect_all();
      vm.treeInstance
        .jstree(true)
        .get_json('#', {flat: true})
        .forEach(function(item) {
          var fullItem = vm.treeInstance.jstree(true).get_node(item.id);
          if (fullItem.original.id == node.id) {
            vm.treeInstance.jstree(true).select_node(item);
          }
        });
    };

    vm.refreshSelected = function() {
      vm.getNode(vm.selected.id).then(function(node) {
        vm.setSelected(node);
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

        vm.getTags(vm.selected, {
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

    vm.getTags = function(location, params) {
      return $http
        .get(appConfig.djangoUrl + 'locations/' + location.id + '/tags/', {params: params})
        .then(function(response) {
          return response;
        });
    };

    vm.addNodeModal = function(node) {
      var modalInstance = $uibModal.open({
        animation: true,
        ariaLabelledBy: 'modal-title',
        ariaDescribedBy: 'modal-body',
        templateUrl: 'static/frontend/views/add_location_modal.html',
        size: 'lg',
        controller: 'LocationModalInstanceCtrl',
        controllerAs: '$ctrl',
        resolve: {
          data: {
            parent: node ? node.id : null,
          },
        },
      });
      modalInstance.result.then(
        function(data) {
          vm.buildTree();
        },
        function() {
          $log.info('modal-component dismissed at: ' + new Date());
        }
      );
    };

    vm.editNodeModal = function(node) {
      var modalInstance = $uibModal.open({
        animation: true,
        ariaLabelledBy: 'modal-title',
        ariaDescribedBy: 'modal-body',
        templateUrl: 'static/frontend/views/edit_location_modal.html',
        size: 'lg',
        controller: 'LocationModalInstanceCtrl',
        controllerAs: '$ctrl',
        resolve: {
          data: {
            location: node,
          },
        },
      });
      modalInstance.result.then(
        function(data) {
          vm.buildTree().then(function() {
            vm.refreshSelected();
          });
        },
        function() {
          $log.info('modal-component dismissed at: ' + new Date());
        }
      );
    };

    vm.removeNodeModal = function(node) {
      var modalInstance = $uibModal.open({
        animation: true,
        ariaLabelledBy: 'modal-title',
        ariaDescribedBy: 'modal-body',
        templateUrl: 'static/frontend/views/remove_location_modal.html',
        size: 'lg',
        controller: 'LocationModalInstanceCtrl',
        controllerAs: '$ctrl',
        resolve: {
          data: {
            location: node,
            allow_close: true,
            remove: true,
          },
        },
      });
      modalInstance.result.then(
        function(data) {
          if (node.id === vm.selected.id) {
            vm.treeInstance.jstree(true).deselect_all();
            vm.selected = null;
          }
          vm.buildTree();
        },
        function() {
          $log.info('modal-component dismissed at: ' + new Date());
        }
      );
    };
  });
