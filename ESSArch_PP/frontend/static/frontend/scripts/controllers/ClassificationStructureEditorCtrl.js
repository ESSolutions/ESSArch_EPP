angular
  .module('essarch.controllers')
  .controller('ClassificationStructureEditorCtrl', function(
    $scope,
    $http,
    appConfig,
    Notifications,
    $uibModal,
    $log,
    $translate,
    Structure,
    $q,
    $timeout,
    $state,
    $stateParams
  ) {
    var vm = this;
    vm.structure = null;
    vm.structures = [];
    vm.rules = {};
    vm.manuallyReload = false;
    $scope.angular = angular;
    vm.structureTypes = [];
    vm.structureType = null;
    vm.$onInit = function() {
      $http.get(appConfig.djangoUrl + 'structure-types/', {params: {pager: 'none'}}).then(function(response) {
        vm.structureTypes = [{name: $translate.instant('ACCESS.SEE_ALL'), id: null}].concat(response.data);
      });
      if ($stateParams != null && $stateParams.id) {
        vm.structureClick({id: $stateParams.id});
      }
    };

    vm.structureClick = function(row) {
      if (vm.structure && vm.structure.id === row.id) {
        vm.structure = null;
        $state.go($state.current.name, {id: null}, {notify: false});
      } else {
        vm.structuresLoading = true;
        Structure.get({id: row.id}).$promise.then(function(resource) {
          vm.structuresLoading = false;
          vm.structure = resource;
          $state.go($state.current.name, {id: vm.structure.id}, {notify: false});
          vm.oldStructure = angular.copy(resource);
          vm.rules = vm.structure.specification.rules ? angular.copy(vm.structure.specification.rules) : {};
          var typePromises = [];
          typePromises.push(
            $http
              .get(appConfig.djangoUrl + 'tag-version-types/', {params: {archive_type: false, pager: 'none'}})
              .then(function(response) {
                return response.data;
              })
          );
          typePromises.push(
            $http
              .get(appConfig.djangoUrl + 'structure-unit-types/', {
                params: {structure_type: vm.structure.type.id, pager: 'none'},
              })
              .then(function(response) {
                return response.data;
              })
          );
          $q.all(typePromises).then(function(data) {
            vm.typeOptions = [].concat.apply([], data);
            if (vm.typeOptions.length > 0) {
              vm.newRule = vm.typeOptions.length > 0 ? vm.typeOptions[0].name : null;
            }
          });
          vm.getTree(vm.structure).then(function(tree) {
            vm.recreateTree(tree);
          });
        });
      }
    };

    vm.treeReady = function() {};

    vm.updateStructures = function() {
      return vm.getStructures($scope.tableState);
    };

    vm.getStructures = function(tableState) {
      vm.structuresLoading = true;
      if (vm.structures.length == 0) {
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
        return Structure.query({
          page: pageNumber,
          page_size: number,
          ordering: sortString,
          search: search,
          is_template: true,
          type: vm.structureType,
        }).$promise.then(function(resource) {
          vm.structures = resource;
          tableState.pagination.numberOfPages = Math.ceil(resource.$httpHeaders('Count') / number); //set the number of pages so the pagination can update
          $scope.initLoad = false;
          vm.structuresLoading = false;
          return resource;
        });
      }
    };

    // Tree

    vm.structureTreeData = [];
    var newId = 1;
    vm.ignoreStructureChanges = false;
    vm.newNode = {};

    vm.getTree = function(structure) {
      structure.structureType = angular.copy(structure.type);
      var rootNode = angular.extend(structure, {
        text: structure.name,
        a_attr: {
          title: structure.name,
        },
        root: true,
        type: 'archive',
      });
      return $http
        .get(appConfig.djangoUrl + 'structures/' + structure.id + '/tree/')
        .then(function(response) {
          var tree = response.data;
          if (tree.length <= 0) {
            return [rootNode];
          }
          tree.forEach(function(x) {
            prepareTree(x);
          });
          rootNode.children = tree;
          rootNode.state = {opened: true};
          var finalTree = [rootNode];
          return finalTree;
        })
        .catch(function(response) {
          return [rootNode];
        });
    };

    function prepareTree(current, depth) {
      current = createChild(current);
      if (current.children && current.children.length) {
        for (var i = 0; i < current.children.length; i++) {
          prepareTree(current.children[i], depth + 1);
        }
      }
    }

    createChild = function(child) {
      if (angular.isUndefined(child.name)) {
        child.name = '';
      }
      child.text = '<b>' + (child.reference_code ? child.reference_code : '') + '</b> ' + child.name;
      child.a_attr = {
        title: child.name,
      };
      child.original_parent = angular.copy(child.parent);
      delete child.parent;
      child.state = {opened: true};
      return child;
    };

    vm.selectRoot = function() {
      if (vm.manuallyReload) {
        var node = vm.structureTreeInstance
          .jstree(true)
          .get_json('#', {flat: true})
          .filter(function(item) {
            return item.id == vm.manuallyReload.id;
          })[0];
        vm.structureTreeInstance.jstree(true).select_node(node);
        vm.manuallyReload = false;
      } else {
        var tree = vm.structureTreeInstance.jstree(true);
        tree.deselect_all();
        tree.select_node(tree.get_json('#')[0]);
      }
    };

    vm.getStructureUnit = function(id) {
      return $http
        .get(appConfig.djangoUrl + 'structure-units/' + id + '/', {
          params: {
            structure: vm.structure.id,
          },
        })
        .then(function(response) {
          return response.data;
        });
    };

    vm.updateStructureUnit = function() {
      if (!vm.node.root) {
        vm.getStructureUnit(vm.node.id).then(function(node) {
          vm.node = node;
        });
      } else {
        vm.getStructures(vm.tableState);
      }
    };

    vm.structureTreeChange = function(jqueryobj, e) {
      if (e.action === 'select_node') {
        vm.nodeLoading = true;
        if (!e.node.original.root) {
          vm.getStructureUnit(e.node.original.id).then(function(node) {
            vm.nodeLoading = false;
            vm.node = node;
          });
        } else {
          vm.node = e.node.original;
        }
      }
    };

    vm.expandChildren = function(jqueryobj, e, reload) {
      if (e.action === 'select node') {
        vm.node = e.node.original;
      }
    };

    function getNodeById(node, id) {
      var reduce = [].reduce;
      function runner(result, node) {
        if (result || !node) return result;
        return (
          (node.id === id && node) || //is this the proper node?
          runner(null, node.children) || //process this nodes children
          reduce.call(Object(node), runner, result)
        ); //maybe this is some ArrayLike Structure
      }
      return runner(null, node);
    }

    /**
     * Tree config for Record tree
     */
    vm.structureTreeConfig = {
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
        archive: {
          icon: 'fas fa-archive',
        },
        document: {
          icon: 'far fa-file',
        },
        plus: {
          icon: 'fas fa-plus',
        },
      },
      dnd: {
        is_draggable: function(nodes) {
          return !vm.structure.published;
        },
      },
      contextmenu: {
        items: function(node, callback) {
          var update = {
            label: $translate.instant('EDIT'),
            action: function update() {
              if (node.original.root) {
                vm.editStructureModal(node.original);
              } else {
                vm.editNodeModal(node.original);
              }
            },
          };
          var add = {
            label: $translate.instant('ADD'),
            action: function() {
              vm.addNodeModal(node.original, vm.structure);
            },
          };
          var addRelation = {
            label: $translate.instant('ACCESS.ADD_RELATION'),
            _disabled: node.original.root,
            action: function() {
              vm.addNodeRelationModal(node.original);
            },
          };
          var remove = {
            label: $translate.instant('REMOVE'),
            _disabled: node.original.root,
            action: function() {
              vm.removeNodeModal(node, vm.structure);
            },
          };
          var actions = {
            update: !vm.structure.published ? update : undefined,
            add: !vm.structure.published ? add : undefined,
            addRelation: !vm.structure.published ? addRelation : undefined,
            remove: !vm.structure.published ? remove : undefined,
          };
          callback(actions);
          return actions;
        },
      },
      version: 1,
      plugins: ['types', 'contextmenu', 'dnd'],
    };

    vm.dropNode = function(jqueryObj, data) {
      var node = data.node.original;
      var parent = vm.structureTreeInstance.jstree(true).get_node(data.parent);
      $http({
        method: 'PATCH',
        url: appConfig.djangoUrl + 'structures/' + vm.structure.id + '/units/' + node.id + '/',
        data: {
          parent: parent.original.root ? null : parent.original.id,
        },
      })
        .then(function(response) {})
        .catch(function(response) {
          Notifications.add('Could not be moved', 'error');
        });
    };

    vm.applyStructureModelChanges = function() {
      return !vm.ignoreStructureChanges;
    };

    vm.recreateTree = function(tags) {
      vm.ignoreStructureChanges = true;
      if (angular.equals(tags, vm.structureTreeData)) {
        vm.structureTreeConfig.version++;
      } else {
        vm.structureTreeData = angular.copy(tags);
        vm.structureTreeConfig.version++;
      }
    };

    // Rules
    vm.newRule = null;
    vm.addRule = function(name) {
      if (name !== null) {
        vm.rules[name] = {
          movable: true,
        };
        vm.newRule = vm.typeOptions.length > 0 ? vm.typeOptions[0].name : null;
      }
    };
    vm.savingRules = false;
    vm.saveRules = function(rules, structure) {
      vm.savingRules = true;
      Structure.update(
        {
          id: structure.id,
        },
        {
          specification: {
            rules: rules,
          },
        }
      ).$promise.then(function(resource) {
        vm.structure = resource;
        vm.rules = resource.specification.rules ? angular.copy(resource.specification.rules) : {};
        vm.savingRules = false;
      });
    };

    vm.savingSettings = false;
    vm.saveSettings = function(structure) {
      vm.savingSettings = true;
      Structure.update(
        {
          id: structure.id,
        },
        {
          start_date: vm.structure.start_date,
          end_date: vm.structure.end_date,
          level: vm.structure.level,
        }
      ).$promise.then(function(resource) {
        vm.structure = resource;
        vm.oldStructure = angular.copy(resource);
        vm.rules = resource.specification.rules ? angular.copy(resource.specification.rules) : {};
        vm.savingSettings = false;
        Notifications.add($translate.instant('SETTINGS_SAVED'), 'success');
      });
    };

    vm.removeRule = function(rule) {
      if (vm.rules[rule]) {
        delete vm.rules[rule];
      }
    };

    // Modals
    vm.publishModal = function(node) {
      var modalInstance = $uibModal.open({
        animation: true,
        ariaLabelledBy: 'modal-title',
        ariaDescribedBy: 'modal-body',
        templateUrl: 'static/frontend/views/publish_structure_modal.html',
        controller: 'PublishClassificationStructureCtrl',
        controllerAs: '$ctrl',
        size: 'lg',
        resolve: {
          data: {
            node: node,
            rules: vm.rules,
            structure: vm.structure,
          },
        },
      });
      modalInstance.result.then(
        function(data, $ctrl) {
          vm.updateStructures().then(function() {
            vm.structure = null;
            $timeout(function() {
              vm.structureClick(node);
            });
          });
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
        templateUrl: 'static/frontend/views/edit_structure_unit_node_modal.html',
        controller: 'EditStructureUnitModalInstanceCtrl',
        controllerAs: '$ctrl',
        size: 'lg',
        resolve: {
          data: {
            node: node,
            structure: vm.structure,
          },
        },
      });
      modalInstance.result.then(
        function(data, $ctrl) {
          vm.getTree(vm.structure).then(function(tree) {
            vm.manuallyReload = vm.node;
            vm.recreateTree(tree);
          });
        },
        function() {
          $log.info('modal-component dismissed at: ' + new Date());
        }
      );
    };
    vm.addNodeModal = function(node, structure) {
      var modalInstance = $uibModal.open({
        animation: true,
        ariaLabelledBy: 'modal-title',
        ariaDescribedBy: 'modal-body',
        templateUrl: 'static/frontend/views/add_node_modal.html',
        controller: 'ClassificationModalInstanceCtrl',
        controllerAs: '$ctrl',
        size: 'lg',
        resolve: {
          data: {
            node: node,
            structure: structure,
            children: getNodeById(vm.structureTreeData[0], node.id).children,
          },
        },
      });
      modalInstance.result.then(
        function(data, $ctrl) {
          vm.getTree(vm.structure).then(function(tree) {
            vm.manuallyReload = data;
            vm.recreateTree(tree);
          });
        },
        function() {
          $log.info('modal-component dismissed at: ' + new Date());
        }
      );
    };

    vm.removeNodeModal = function(node, structure) {
      var modalInstance = $uibModal.open({
        animation: true,
        ariaLabelledBy: 'modal-title',
        ariaDescribedBy: 'modal-body',
        templateUrl: 'static/frontend/views/remove_node_modal.html',
        controller: 'ClassificationModalInstanceCtrl',
        controllerAs: '$ctrl',
        size: 'lg',
        resolve: {
          data: {
            node: node,
            structure: structure,
          },
        },
      });
      modalInstance.result.then(
        function(data, $ctrl) {
          vm.structureTreeInstance.jstree(true).delete_node(node.id);
          vm.structureTreeInstance.jstree(true).select_node(node.parent);
        },
        function() {
          $log.info('modal-component dismissed at: ' + new Date());
        }
      );
    };

    vm.removeStructureModal = function(structure) {
      var modalInstance = $uibModal.open({
        animation: true,
        ariaLabelledBy: 'modal-title',
        ariaDescribedBy: 'modal-body',
        templateUrl: 'static/frontend/views/remove_structure_modal.html',
        controller: 'ClassificationModalInstanceCtrl',
        controllerAs: '$ctrl',
        size: 'lg',
        resolve: {
          data: {
            structure: structure,
          },
        },
      });
      modalInstance.result.then(
        function(data, $ctrl) {
          vm.structure = null;
          vm.updateStructures();
        },
        function() {
          $log.info('modal-component dismissed at: ' + new Date());
        }
      );
    };

    vm.newStructureModal = function() {
      var modalInstance = $uibModal.open({
        animation: true,
        ariaLabelledBy: 'modal-title',
        ariaDescribedBy: 'modal-body',
        templateUrl: 'static/frontend/views/new_structure_modal.html',
        size: 'lg',
        controller: 'ClassificationModalInstanceCtrl',
        controllerAs: '$ctrl',
        resolve: {
          data: {
            newStructure: true,
          },
        },
      });
      modalInstance.result.then(
        function(data) {
          vm.updateStructures();
        },
        function() {
          $log.info('modal-component dismissed at: ' + new Date());
        }
      );
    };

    vm.editStructureModal = function(structure) {
      var modalInstance = $uibModal.open({
        animation: true,
        ariaLabelledBy: 'modal-title',
        ariaDescribedBy: 'modal-body',
        templateUrl: 'static/frontend/views/edit_structure_modal.html',
        size: 'lg',
        controller: 'ClassificationModalInstanceCtrl',
        controllerAs: '$ctrl',
        resolve: {
          data: {
            structure: structure,
          },
        },
      });
      modalInstance.result.then(
        function(data) {
          vm.structure = null;
          $timeout(function() {
            vm.structureClick(structure);
          });
        },
        function() {
          $log.info('modal-component dismissed at: ' + new Date());
        }
      );
    };

    vm.addNodeRelationModal = function(node) {
      var modalInstance = $uibModal.open({
        animation: true,
        ariaLabelledBy: 'modal-title',
        ariaDescribedBy: 'modal-body',
        templateUrl: 'static/frontend/views/add_structure_unit_relation_modal.html',
        size: 'lg',
        controller: 'StructureUnitRelationModalInstanceCtrl',
        controllerAs: '$ctrl',
        resolve: {
          data: {
            node: node,
            structure: vm.structure,
          },
        },
      });
      modalInstance.result.then(
        function(data) {
          if (node.id === vm.node.id) {
            vm.updateStructureUnit();
          } else {
            vm.structureTreeInstance.jstree(true).deselect_all();
            vm.structureTreeInstance.jstree(true).select_node(node);
          }
          vm.updateStructures();
        },
        function() {
          $log.info('modal-component dismissed at: ' + new Date());
        }
      );
    };

    vm.editNodeRelationModal = function(relation, node) {
      var modalInstance = $uibModal.open({
        animation: true,
        ariaLabelledBy: 'modal-title',
        ariaDescribedBy: 'modal-body',
        templateUrl: 'static/frontend/views/edit_structure_unit_relation_modal.html',
        size: 'lg',
        controller: 'StructureUnitRelationModalInstanceCtrl',
        controllerAs: '$ctrl',
        resolve: {
          data: {
            relation: relation,
            node: node,
            structure: vm.structure,
          },
        },
      });
      modalInstance.result.then(
        function(data) {
          if (node.id === vm.node.id) {
            vm.updateStructureUnit();
          } else {
            vm.structureTreeInstance.jstree(true).deselect_all();
            vm.structureTreeInstance.jstree(true).select_node(node);
          }
          vm.updateStructures();
        },
        function() {
          $log.info('modal-component dismissed at: ' + new Date());
        }
      );
    };

    vm.removeNodeRelationModal = function(relation, node) {
      var modalInstance = $uibModal.open({
        animation: true,
        ariaLabelledBy: 'modal-title',
        ariaDescribedBy: 'modal-body',
        templateUrl: 'static/frontend/views/remove_structure_unit_relation_modal.html',
        size: 'lg',
        controller: 'StructureUnitRelationModalInstanceCtrl',
        controllerAs: '$ctrl',
        resolve: {
          data: {
            relation: relation,
            node: node,
            structure: vm.structure,
          },
        },
      });
      modalInstance.result.then(
        function(data) {
          if (node.id === vm.node.id) {
            vm.updateStructureUnit();
          } else {
            vm.structureTreeInstance.jstree(true).deselect_all();
            vm.structureTreeInstance.jstree(true).select_node(node);
          }
          vm.updateStructures();
        },
        function() {
          $log.info('modal-component dismissed at: ' + new Date());
        }
      );
    };

    vm.removeStructureRuleModal = function(type, value, structure) {
      var rule = {
        key: type,
        value: value,
      };
      var modalInstance = $uibModal.open({
        animation: true,
        ariaLabelledBy: 'modal-title',
        ariaDescribedBy: 'modal-body',
        templateUrl: 'static/frontend/views/remove_structure_rule_modal.html',
        size: 'md',
        controller: 'StructureRuleModalCtrl',
        controllerAs: '$ctrl',
        resolve: {
          data: {
            remove: true,
            rule: rule,
            rules: vm.rules,
            structure: structure,
          },
        },
      });
      modalInstance.result.then(
        function(data) {
          vm.updateStructures().then(function() {
            vm.structure.specification = data.specification;
            vm.node.specification = data.specification;
            if (data.specification.rules) {
              vm.rules = data.specification.rules;
            }
          });
        },
        function() {
          $log.info('modal-component dismissed at: ' + new Date());
        }
      );
    };
    vm.addStructureRuleModal = function(structure) {
      var modalInstance = $uibModal.open({
        animation: true,
        ariaLabelledBy: 'modal-title',
        ariaDescribedBy: 'modal-body',
        templateUrl: 'static/frontend/views/add_structure_rule_modal.html',
        size: 'md',
        controller: 'StructureRuleModalCtrl',
        controllerAs: '$ctrl',
        resolve: {
          data: {
            rules: vm.rules,
            structure: structure,
          },
        },
      });
      modalInstance.result.then(
        function(data) {
          vm.updateStructures().then(function() {
            vm.structure.specification = data.specification;
            vm.node.specification = data.specification;
            if (data.specification.rules) {
              vm.rules = data.specification.rules;
            }
          });
        },
        function() {
          $log.info('modal-component dismissed at: ' + new Date());
        }
      );
    };
  });
