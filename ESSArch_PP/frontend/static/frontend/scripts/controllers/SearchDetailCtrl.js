angular.module('myApp').controller('SearchDetailCtrl', function($scope, $stateParams,Search, $q, $scope, $http, $rootScope, appConfig, $log, $timeout, TopAlert, $sce, $translate, $anchorScroll, $uibModal, PermPermissionStore, $window, $state) {
    var vm = this;
    $scope.angular = angular;
    vm.url = appConfig.djangoUrl;
    vm.$onInit = function() {
        vm.loadRecordAndTree($state.current.name.split(".").pop(), $stateParams.id);
    }

    vm.loadRecordAndTree = function(index, id) {
        vm.viewContent = true;
        $http.get(vm.url+"search/"+ index +"/"+id+"/").then(function(response) {
            vm.record = response.data;
            $rootScope.$broadcast('UPDATE_TITLE', {title: vm.record._source.name});
            vm.activeTab = 1;
            vm.buildRecordTree(response.data).then(function(node) {
                var treeData = [node];
                vm.recreateRecordTree(treeData);
            })
            vm.record.children = [];//[{text: "", parent: vm.record.id, placeholder: true, icon: false, state: {disabled: true}}];
            if (angular.isUndefined(vm.record._source.terms_and_condition)) {
                vm.record._source.terms_and_condition = null;
            }
            getChildren(vm.record).then(function (response) {
                vm.record_children = response.data;
            })
        });
    }

    vm.currentItem = null;

    $scope.checkPermission = function(permissionName) {
        return !angular.isUndefined(PermPermissionStore.getPermissionDefinition(permissionName));
    };

    vm.getPathFromParents = function(tag) {
        if(tag.parents.length > 0) {
            vm.getTag(tag.parents[0]);
        }
    }

    vm.getTag = function(tag) {
        return $http.get(vm.url+"search/"+tag._index+"/"+tag._id+"/").then(function(response) {
            return response.data;
        });
    }

    createChild = function(child) {
        if (angular.isUndefined(child._source.name)) {
            child._source.name = "";
        }
        child.text = "<b>" + (child._source.reference_code ? child._source.reference_code : "") + "</b> " + child._source.name;
        if (!child.children) {
            child.children = [{ text: "", parent: child._id, placeholder: true, icon: false, state: { disabled: true } }];
        }
        child.state = { opened: false };
        return child;
    }

    vm.buildRecordTree = function(startNode) {
        if(angular.isUndefined(startNode._source.name)) {
            startNode._source.name = "";
        }
        startNode.text = "<b>" + (startNode._source.reference_code ? startNode._source.reference_code : "") + "</b> " + startNode._source.name;
        startNode.state = {opened: true};
        if(startNode._source.link_id == vm.record._source.link_id) {
            startNode.state.selected = true;
        }
        if (!startNode.children || startNode.children.length <= 0) {
            var startNodePromise = getChildren(startNode).then(function (start_node_children) {

                start_node_children.data.forEach(function (child) {
                    child = createChild(child);
                    startNode.children.push(child);
                });

                if (start_node_children.data.length < start_node_children.count) {
                    startNode.children.push({
                        text: $translate.instant("SEE_MORE"),
                        see_more: true,
                        type: "plus",
                        _source: {
                            parent: {id: startNode._id, index: startNode._index},
                        }
                    });
                    if (!getNodeById(startNode, startNode._id)) {
                        startNode.state.opened = false;
                        startNode.children.push(startNode);
                    }
                }
            });
        }
        if (startNode._source.parent) {
            var parentPromise = $http.get(vm.url + "search/"+startNode._source.parent.index + "/" + startNode._source.parent.id + "/").then(function (response) {
                var p = response.data;
                p.children = [];
                return getChildren(p).then(function (children) {
                    children.data.forEach(function (child) {
                        if (child._source.link_id == startNode._source.link_id) {
                            p.children.push(startNode);
                        } else {
                            child = createChild(child);
                            p.children.push(child);
                        }
                    });
                    if (children.data.length < children.count) {
                        p.children.push({
                            text: $translate.instant("SEE_MORE"),
                            see_more: true,
                            type: "plus",
                            _source: {
                                parent: {id: p._id, index: p._index},
                            }
                        });
                        if (!getNodeById(p, startNode._id)) {
                            startNode.state.opened = false;
                            p.children.push(startNode);
                        }
                    }
                    return vm.buildRecordTree(p);
                })
            });
        } else {
            var defer = $q.defer();
            defer.resolve(startNode);
            var parentPromise = defer.promise;
        }
        return $q.all([parentPromise, startNodePromise]).then(function(result) {
            return result[0];
        })
    }
    function getChildren(node) {
        return $http.get(vm.url+"search/"+node._index+"/"+node._id+"/children/", {params: {page_size: 10, page: 1}}).then(function(response) {
            var count = response.headers('Count');
            return {
                data: response.data,
                count: count
            }
        });
    }

    var newId = 1;
    vm.ignoreChanges = false;
    vm.ignoreRecordChanges = false;
    vm.newNode = {};

    vm.applyRecordModelChanges = function() {
        return !vm.ignoreRecordChanges;
    };

    /**
     * Recreates record tree with given tags.
     * Version variable is updated so that the tree will detect
     * a change in the configuration object, desroy and rebuild with data from vm.tags
     */
    vm.recreateRecordTree = function(tags) {
        vm.ignoreRecordChanges = true;
        if(angular.equals(tags, vm.recordTreeData)) {
            vm.recordTreeConfig.version++;
        } else {
            angular.copy(tags, vm.recordTreeData);
            vm.recordTreeConfig.version++;
        }
    }

    /**
     * Tree config for Record tree
     */
    vm.recordTreeConfig = {
        core : {
            multiple : false,
            animation: 50,
            error : function(error) {
                $log.error('treeCtrl: error from js tree - ' + angular.toJson(error));
            },
            check_callback : true,
            worker : true,
        },
        types : {
            default : {
                icon: 'fa fa-folder-o'
            },
            archive : {
                icon : 'fa fa-archive'
            },
            plus: {
                icon: "fa fa-plus"
            }
        },
        contextmenu: {
            items: function (node, callback) {
                var update = {
                    label: $translate.instant('UPDATE'),
                    action: function () {
                        vm.editNodeModal(node);
                    },
                };
                var add = {
                    label: $translate.instant('ADD'),
                    action: function () {
                        vm.addNodeModal(node);
                    },
                };
                var remove = {
                    label: $translate.instant('REMOVE'),
                    action: function () {
                        vm.removeNodeModal(node);
                    },
                };
                var newVersion = {
                    label: $translate.instant('NEW_VERSION'),
                    action: function() {
                        vm.newVersionNodeModal(node);
                    }
                }
                var actions = { update: update, add: add, remove: remove, newVersion: newVersion };
                callback(actions);
                return actions;
            }
        },
        version: 1,
        plugins : ['types', 'contextmenu', 'dnd']
    };

    vm.dropNode = function(jqueryObj, data) {
        var node = data.node.original;
        var parent = vm.recordTreeInstance.jstree(true).get_node(data.parent);
        Search.updateNode(node,{"parent.id": parent.original._id, "parent.index": parent.original._index}, true).then(function(response) {
            vm.loadRecordAndTree(parent.original._index, parent.original._id);
        }).catch(function(response) {
            TopAlert.add("Could not be moved", "error");
        })
    }

    vm.setType = function() {
        var array = vm.recordTreeInstance.jstree(true).get_json("#", {flat: true}).forEach(function(item) {
            var fullItem = vm.recordTreeInstance.jstree(true).get_node(item.id);
            if(fullItem.original._index == "archive") {
                vm.recordTreeInstance.jstree(true).set_type(item, "archive");
            }
        });
    }

    vm.recordTreeData = [];
    vm.selectRecord = function (jqueryobj, e) {
        if(e.node && e.node.original.see_more) {
            var tree = vm.recordTreeData;
            var parent = vm.recordTreeInstance.jstree(true).get_node(e.node.parent);
            var children = tree.map(function(x) {return getNodeById(x, parent.original._id); })[0].children;
            $http.get(vm.url+"search/"+e.node.original._source.parent.index+"/"+e.node.original._source.parent.id+"/children/", {params: {page_size: 10, page: Math.ceil(children.length/10)}}).then(function(response) {
                var count = response.headers('Count');
                var selectedElement = null;
                var see_more = null;
                if(children[children.length-1].see_more) {
                    see_more = children.pop();
                } else {
                    selectedElement = children.pop();
                    see_more = children.pop();
                }
                response.data.forEach(function(child) {
                    child = createChild(child);
                    children.push(child);
                });
                if(children.length < count) {
                    children.push(see_more);
                    if(selectedElement) {
                        var resultInChildren = getNodeById(children, selectedElement._id);
                        if(!resultInChildren) {
                            selectedElement.state.opened = false;
                            children.push(selectedElement);
                        } else {
                            resultInChildren.state.selected = true;
                        }
                    }
                }
                vm.recreateRecordTree(tree);
            });
            return;
        }
        if (e.action == "select_node") {
            vm.record = e.node.original;
            $state.go("home.search."+vm.record._index, {id: vm.record._id}, {notify: false});
            $rootScope.$broadcast('UPDATE_TITLE', {title: vm.record._source.name});
            if(angular.isUndefined(vm.record._source.terms_and_condition)) {
                vm.record._source.terms_and_condition = null;
            }
            vm.record.children = [{text: "", parent: vm.record._id, placeholder: true, icon: false, state: {disabled: true}}];
            getChildren(vm.record).then(function(response) {
                vm.record_children = response.data;
            })
        }
    }

    vm.expandChildren = function (jqueryobj, e, reload) {
        var tree = vm.recordTreeData;
        var parent = tree.map(function(x) {return getNodeById(x, e.node.original._id); })[0];
        var children = tree.map(function(x) {return getNodeById(x, parent._id); })[0].children;
        if(e.node.children.length < 2 || reload) {
            $http.get(vm.url+"search/"+e.node.original._index+"/"+e.node.original._id+"/children/", {params: {page_size: 10, page: Math.ceil(children.length/10)}}).then(function(response) {
                var count = response.headers('Count');
                children.pop();
                response.data.forEach(function(child) {
                    child = createChild(child);
                    children.push(child);
                });
                if(children.length < count) {
                    children.push({
                        text: $translate.instant("SEE_MORE"),
                        see_more: true,
                        type: "plus",
                        _source: {
                            parent: {id: parent._id, index: parent._index}
                        }
                    });
                }
                parent.state = {opened: true}
                vm.recordTreeConfig.version++;
                return;
            });
        }
    }
    function getNodeById(node, id){
        var reduce = [].reduce;
        function runner(result, node){
            if(result || !node) return result;
            return node._id === id && node || //is this the proper node?
                runner(null, node.children) || //process this nodes children
                reduce.call(Object(node), runner, result);  //maybe this is some ArrayLike Structure
        }
        return runner(null, node);
    }

    vm.viewFile = function(file) {
        var params = {};
        if(file.href != "") {
            params.path = file.href+"/"+file.name;
        } else {
            params.path = file.name;
        }
        var showFile = $sce.trustAsResourceUrl(appConfig.djangoUrl + "information-packages/"+file.ip+"/files/?path="+params.path);
        $window.open(showFile, '_blank');
    }

    vm.editField = function(key, value) {
        var modalInstance = $uibModal.open({
            animation: true,
            ariaLabelledBy: 'modal-title',
            ariaDescribedBy: 'modal-body',
            templateUrl: 'static/frontend/views/edit_field_modal.html',
            scope: $scope,
            controller: 'ModalInstanceCtrl',
            controllerAs: '$ctrl',
            size: "lg",
            resolve: {
                data: {
                    field: {
                        key: key,
                        value: value
                    }
                }
            }
        });
        modalInstance.result.then(function (data) {
            delete vm.record[key]
            vm.record[data.key] = data.value;
            TopAlert.add( "Fältet: " + data.key + ", har ändrats i: " + vm.record.name, "success");
        }, function () {
            $log.info('modal-component dismissed at: ' + new Date());
        });
    }

    vm.addField = function(key, value) {
        var modalInstance = $uibModal.open({
            animation: true,
            ariaLabelledBy: 'modal-title',
            ariaDescribedBy: 'modal-body',
            templateUrl: 'static/frontend/views/add_field_modal.html',
            scope: $scope,
            controller: 'ModalInstanceCtrl',
            controllerAs: '$ctrl',
            size: "lg",
            resolve: {
                data: {
                    field: {
                        key: "",
                        value: ""
                    }
                }
            }
        });
        modalInstance.result.then(function (data) {
            vm.record[data.key] = data.value;
            TopAlert.add( "Fältet: " + data.key + ", har lagts till i: " + vm.record.name, "success");
        }, function () {
            $log.info('modal-component dismissed at: ' + new Date());
        });
    }

    vm.removeField = function(field) {
        var modalInstance = $uibModal.open({
            animation: true,
            ariaLabelledBy: 'modal-title',
            ariaDescribedBy: 'modal-body',
            templateUrl: 'static/frontend/views/delete_field_modal.html',
            scope: $scope,
            controller: 'ModalInstanceCtrl',
            controllerAs: '$ctrl',
            resolve: {
                data: {
                    field: field
                }
            }
        });
        modalInstance.result.then(function (data, $ctrl) {
            delete vm.record[field];
            TopAlert.add( "Fältet: " + field + ", har tagits bort från: " + vm.record.name, "success");
        }, function () {
            $log.info('modal-component dismissed at: ' + new Date());
        });

    }

    vm.viewResult = function() {
        var modalInstance = $uibModal.open({
            animation: true,
            ariaLabelledBy: 'modal-title',
            ariaDescribedBy: 'modal-body',
            templateUrl: 'static/frontend/views/universal_viewer_modal.html',
            scope: $scope,
            controller: 'ModalInstanceCtrl',
            controllerAs: '$ctrl',
            size: "lg",
            resolve: {
                data: {}
            }
        });
        modalInstance.result.then(function (data, $ctrl) {
        }, function () {
            $log.info('modal-component dismissed at: ' + new Date());
        });
    }

    vm.editNodeModal = function(node) {
        var modalInstance = $uibModal.open({
            animation: true,
            ariaLabelledBy: 'modal-title',
            ariaDescribedBy: 'modal-body',
            templateUrl: 'static/frontend/views/edit_node_modal.html',
            controller: 'EditNodeModalInstanceCtrl',
            controllerAs: '$ctrl',
            size: "lg",
            resolve: {
                data: {
                    node: node
                }
            }
        });
        modalInstance.result.then(function (data, $ctrl) {
            vm.loadRecordAndTree(node.original._index, node.original._id);
        }, function () {
            $log.info('modal-component dismissed at: ' + new Date());
        });
    }
    vm.addNodeModal = function(node) {
        var modalInstance = $uibModal.open({
            animation: true,
            ariaLabelledBy: 'modal-title',
            ariaDescribedBy: 'modal-body',
            templateUrl: 'static/frontend/views/add_node_modal.html',
            controller: 'AddNodeModalInstanceCtrl',
            controllerAs: '$ctrl',
            size: "lg",
            resolve: {
                data: {
                    node: node
                }
            }
        });
        modalInstance.result.then(function (data, $ctrl) {
            vm.loadRecordAndTree(data._index, data._id);
        }, function () {
            $log.info('modal-component dismissed at: ' + new Date());
        });
    }
    vm.newVersionNodeModal = function(node) {
        var modalInstance = $uibModal.open({
            animation: true,
            ariaLabelledBy: 'modal-title',
            ariaDescribedBy: 'modal-body',
            templateUrl: 'static/frontend/views/create_new_node_version_modal.html',
            controller: 'VersionModalInstanceCtrl',
            controllerAs: '$ctrl',
            size: "lg",
            resolve: {
                data: {
                    node: node
                }
            }
        });
        modalInstance.result.then(function (data, $ctrl) {
            vm.loadRecordAndTree(node.original._index, node.original._id);
        }, function () {
            $log.info('modal-component dismissed at: ' + new Date());
        });
    }
    vm.removeNodeModal = function(node) {
        var modalInstance = $uibModal.open({
            animation: true,
            ariaLabelledBy: 'modal-title',
            ariaDescribedBy: 'modal-body',
            templateUrl: 'static/frontend/views/remove_node_modal.html',
            controller: 'RemoveNodeModalInstanceCtrl',
            controllerAs: '$ctrl',
            size: "lg",
            resolve: {
                data: {
                    node: node
                }
            }
        });
        modalInstance.result.then(function (data, $ctrl) {
            var parent = vm.recordTreeInstance.jstree(true).get_node(node.parent);
            vm.selectRecord(null, {node: parent});
            vm.loadRecordAndTree(parent.original._index, parent.original._id);
        }, function () {
            $log.info('modal-component dismissed at: ' + new Date());
        });
    }
});
