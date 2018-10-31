angular.module('essarch.controllers').controller('SearchDetailCtrl', function($scope, $controller, $stateParams, Search, $q, $http, $rootScope, appConfig, $log, $timeout, Notifications, $sce, $translate, $anchorScroll, $uibModal, PermPermissionStore, $window, $state, $interval, $filter) {
    var vm = this;
    $controller('TagsCtrl', { $scope: $scope, vm: vm });
    $scope.angular = angular;
    vm.url = appConfig.djangoUrl;
    vm.unavailable = false;
    vm.structure = null;

    // Record update interval
    var recordInterval;

    // Destroy intervals on state change
    $scope.$on('$stateChangeStart', function() {
        $interval.cancel(recordInterval);
    });

    vm.$onInit = function() {
        vm.loadRecordAndTree($state.current.name.split(".").pop(), $stateParams.id).then(function() {
            $interval.cancel(recordInterval);
            recordInterval = $interval(function(){vm.updateRecord()}, appConfig.recordInterval);
        });
    }

    vm.updateRecord = function() {
        vm.childrenLoading = true;
        $http.get(appConfig.djangoUrl + "search/" + vm.record._id + "/", {params: {structure: vm.structure}}).then(function(response) {
            var promises = [];
            promises.push(getBreadcrumbs(vm.record).then(function(list) {
                response.data.breadcrumbs = list;
            }).catch(function(error) {
                Notifications.add('Could not load breadcrumbs!', 'error');
            }));
            promises.push(getChildren(vm.record).then(function (children) {
                vm.record_children = children.data;
                vm.childrenLoading = false;
            }));

            $q.all(promises).then(function(results) {
                vm.record = response.data;
                $rootScope.latestRecord = response.data;
                getVersionSelectData();
            })
        }).catch(function(response) {
            Notifications.add("Could not update record", "error");
        })
    }

    vm.loadRecordAndTree = function(index, id) {
        vm.viewContent = true;
        vm.record_children = [];
        vm.childrenLoading = true;
        return $http.get(vm.url+"search/" + id+"/", {params: {structure: vm.structure}}).then(function(response) {
            vm.record = response.data;
            $rootScope.latestRecord = response.data;
            if(vm.record.structures.length == 0) {
                $scope.getArchives().then(function (result) {
                    vm.tags.archive.options = result;
                });
            }
            if(!vm.structure && vm.record.structures.length > 0) {
                vm.structure = vm.record.structures[vm.record.structures.length-1].id;
            }
            getVersionSelectData();
            $rootScope.$broadcast('UPDATE_TITLE', {title: vm.record.name});
            vm.activeTab = 1;
            vm.buildRecordTree(response.data).then(function(node) {
                var treeData = [node];
                vm.recreateRecordTree(treeData);
            })
            vm.record.children = [];//[{text: "", parent: vm.record.id, placeholder: true, icon: false, state: {disabled: true}}];
            if (angular.isUndefined(vm.record._source.terms_and_condition)) {
                vm.record._source.terms_and_condition = null;
            }
            getBreadcrumbs(vm.record).then(function(list) {
                vm.record.breadcrumbs = list;
            }).catch(function(error) {
                Notifications.add('Could not load breadcrumbs!', 'error');
            })
            getChildren(vm.record).then(function (response) {
                vm.record_children = response.data;
                vm.childrenLoading = false;
            })
            return vm.record;
        }).catch(function(response) {
            if (response.status == 403 || response.status == 404) {
                vm.unavailable = true;
            }
            return vm.record;
        })
    }

    vm.currentItem = null;

    $scope.checkPermission = function(permissionName) {
        return !angular.isUndefined(PermPermissionStore.getPermissionDefinition(permissionName));
    };

    vm.existsForRecord = function(classification) {
        if(vm.record) {
            var temp = false;
            vm.record.structures.forEach(function(structure) {
                if(structure.id == classification) {
                    temp = true;
                }
            })
            return temp;
        }
    }

    vm.getPathFromParents = function(tag) {
        if(tag.parents.length > 0) {
            vm.getTag(tag.parents[0]);
        }
    }

    vm.getTag = function(tag) {
        return $http.get(vm.url+"search/"+tag._id+"/", {params: {structure: vm.structure}}).then(function(response) {
            return response.data;
        });
    }

    createChild = function(child) {
        if (angular.isUndefined(child.name)) {
            child.name = "";
        }
        child.text = "<b>" + (child._source && child._source.reference_code ? child._source.reference_code : "") + "</b> " + child.name;
        child.a_attr = {
            title: child._source.name
        }
        if (!child.is_leaf_node) {
            child.children = [{ text: "", parent: child._id, placeholder: true, icon: false, state: { disabled: true } }];
        }
        child.state = { opened: false };
        return child;
    }

    vm.buildRecordTree = function(startNode) {
        if(angular.isUndefined(startNode.name)) {
            startNode.name = "";
        }
        startNode.text = "<b>" + (startNode._source && startNode._source.reference_code ? startNode._source.reference_code : "") + "</b> " + startNode.name;
        startNode.a_attr = {
            title: startNode._source.name
        }
        startNode.state = {opened: true};
        if(startNode._id == vm.record._id) {
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
                        parent: {id: startNode._id, index: startNode._index},
                        _source: {
                        }
                    });
                    if (!getNodeById(startNode, startNode._id)) {
                        startNode.state.opened = true;
                        startNode.children.push(startNode);
                    }
                }
            });
        }
        if (startNode.parent) {
            var parentPromise = $http.get(vm.url + "search/" + startNode.parent.id + "/", {params: {structure: vm.structure}}).then(function (response) {
                var p = response.data;
                p.children = [];
                return getChildren(p).then(function (children) {
                    children.data.forEach(function (child) {
                        if (child._id == startNode._id) {
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
                            parent: {id: p._id, index: p._index},
                            _source: {
                            }
                        });
                        if (!getNodeById(p, startNode._id)) {
                            startNode.state.opened = true;
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

    function getBreadcrumbs(node) {
        return getParentList([], {index: node._index, id: node._id});
    }
    function getParentList(parentList, parent) {
        return $http.get(vm.url+"search/"+parent.id+"/").then(function(response) {
            if(response.data.parent !== null) {
                parentList.unshift(response.data);
                return getParentList(parentList, response.data.parent);
            } else {
                parentList.unshift(response.data);
                return parentList;
            }
        });
    }

    function getChildren(node) {
        return $http.get(vm.url+"search/"+node._id+"/children/", {params: {page_size: 10, page: 1, structure: vm.structure}}).then(function(response) {
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
     * a change in the configuration object, desroy and rebuild with data from vm.recordTreeData
     */
    vm.recreateRecordTree = function(tags) {
        if(!angular.equals(vm.archiveStructures, tags[0].structures)) {
            vm.archiveStructures = angular.copy(tags[0].structures);
        }
        if(!vm.structure) {
            for(i=vm.archiveStructures.length-1; i>=0; i--) {
                if(vm.existsForRecord(vm.archiveStructures[i].id)) {
                    vm.structure = vm.archiveStructures[i].id;
                    break;
                }
            }
        }
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
            multiple : true,
            animation: 50,
            error : function(error) {
                $log.error('treeCtrl: error from js tree - ' + angular.toJson(error));
            },
            check_callback : true,
            worker : true,
        },
        types : {
            default : {
                icon: 'far fa-folder'
            },
            archive : {
                icon : 'fas fa-archive'
            },
            document : {
                icon : 'far fa-file'
            },
            plus: {
                icon: "fas fa-plus"
            }
        },
        dnd: {
            is_draggable: function(nodes) {
                var structure = null;
                vm.archiveStructures.forEach(function(struct) {
                    if(struct.id === vm.structure) {
                        structure = struct;
                    }
                })
                var type = nodes[0].original.type;
                return _.get(structure, "specification.rules." + type + ".movable", true);
            },
        },
        contextmenu: {
            items: function (node, callback) {
                var update = {
                    label: $translate.instant('UPDATE'),
                    _disabled: function(){
                        return vm.record._source == null
                    },
                    action: function update() {
                        if(vm.record._source) {
                            var selected = vm.recordTreeInstance.jstree(true).get_selected(true).map(function(x) {
                                return x.original;
                            });
                            if(selected.length > 1) {
                                vm.editNodeModal(selected);
                            } else {
                                vm.editNodeModal(vm.record);
                            }
                        }
                    },
                };
                var add = {
                    label: $translate.instant('ADD'),
                    action: function () {
                        vm.addNodeModal(node, vm.structure);
                    },
                };
                var remove = {
                    label: $translate.instant('REMOVE'),
                    action: function () {
                        vm.removeNodeModal(node);
                    },
                };
                var removeFromStructure = {
                    label: $translate.instant('REMOVE_FROM_CLASSIFICATION_STRUCTURE'),
                    action: function () {
                        var struct;
                        vm.archiveStructures.forEach(function(item) {
                            if(item.id == vm.structure) {
                                struct = item;
                            }
                        })
                        vm.removeNodeFromStructureModal(node, struct);
                    },
                };
                var newVersion = {
                    label: $translate.instant('NEW_VERSION'),
                    action: function() {
                        vm.newVersionNodeModal(node);
                    }
                }
                var changeOrganization = {
                    label: $translate.instant('CHANGE_ORGANIZATION'),
                    action: function() {
                        vm.changeOrganizationModal(vm.record);
                    }
                }
                var email = {
                    label: $translate.instant('EMAIL'),
                    action: function() {
                        var selected = vm.recordTreeInstance.jstree(true).get_selected(true).map(function(x) {
                            return x.original;
                        });
                        if(selected.length > 1) {
                            Search.massEmail(selected).then(function(response) {
                                Notifications.add($translate.instant('EMAILS_SENT'), 'success');
                            }).catch(function(response) {
                                if(response.status !== 500) {
                                    Notifications.add($translate.instant('EMAILS_FAILED'), 'error');
                                }
                            })
                        } else if(selected.length == 1) {
                            vm.emailDocument(selected[0]);
                        }
                    }
                }
                var actions = {
                    update: update,
                    add: add,
                    email: email,
                    remove: remove,
                    removeFromStructure: removeFromStructure,
                    newVersion: newVersion,
                    changeOrganization: node.original._index === 'archive'?changeOrganization:null,
                };
                callback(actions);
                return actions;
            }
        },
        version: 1,
        plugins : ['types', 'contextmenu', 'dnd']
    };

    vm.gotoNode = function(node) {
        $state.go("home.access.search." + node._index, { id: node._id });
    }

    vm.dropNode = function(jqueryObj, data) {
        var node = data.node.original;
        var parent = vm.recordTreeInstance.jstree(true).get_node(data.parent);
        Search.updateNode(node,{parent: parent.original._id, structure: vm.structure}, true).then(function(response) {
            vm.loadRecordAndTree(parent.original._index, parent.original._id);
        }).catch(function(response) {
            Notifications.add("Could not be moved", "error");
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

    vm.treeChange = function(jqueryobj, e) {
        if(e.action === "select_node") {
            vm.selectRecord(jqueryobj, e);
        }
    }

    vm.recordTreeData = [];
    vm.selectRecord = function (jqueryobj, e) {
        if(e.node && e.node.original.see_more) {
            var tree = vm.recordTreeData;
            var parent = vm.recordTreeInstance.jstree(true).get_node(e.node.parent);
            var children = tree.map(function(x) {return getNodeById(x, parent.original._id); })[0].children;
            $http.get(vm.url+"search/"+e.node.original.parent.id+"/children/", {params: {structure: vm.structure, page_size: 10, page: Math.ceil(children.length/10)}}).then(function(response) {
                var count = response.headers('Count');
                var selectedElement = null;
                var see_more = null;
                if(children[children.length-1].see_more) {
                    see_more = children.pop();
                    vm.recordTreeInstance.jstree(true).delete_node(e.node.id);
                } else {
                    selectedElement = children.pop();
                    vm.recordTreeInstance.jstree(true).delete_node(parent.children[parent.children.length-1]);
                    see_more = children.pop();
                    vm.recordTreeInstance.jstree(true).delete_node(e.node.id);
                }
                response.data.forEach(function(child) {
                    child = createChild(child);
                    children.push(child);
                    vm.recordTreeInstance.jstree(true).create_node(parent.id, angular.copy(child));
                });
                if(children.length < count) {
                    children.push(see_more);
                    vm.recordTreeInstance.jstree(true).create_node(parent.id, see_more);
                    if(selectedElement) {
                        var resultInChildren = getNodeById(children, selectedElement._id);
                        if(!resultInChildren) {
                            selectedElement.state.opened = true;
                            children.push(selectedElement);
                            vm.recordTreeInstance.jstree(true).create_node(parent.id, selectedElement);
                        } else {
                            resultInChildren.state.selected = true;
                        }
                    }
                }
            });
            return;
        }
        vm.record_children = [];
        vm.childrenLoading = true;
        $http.get(appConfig.djangoUrl + "search/" + e.node.original._id + "/", { params: { structure: vm.structure } }).then(function (response) {
            vm.record = response.data;
            $rootScope.latestRecord = response.data;
            $state.go("home.access.search." + vm.record._index, { id: vm.record._id }, { notify: false });
            $rootScope.$broadcast('UPDATE_TITLE', { title: vm.record.name });

            if (!vm.record.is_leaf_node) {
                vm.record.children = [{ text: "", parent: vm.record._id, placeholder: true, icon: false, state: { disabled: true } }];
            }
            vm.currentVersion = vm.record._id;
            getVersionSelectData();
            getBreadcrumbs(vm.record).then(function(list) {
                vm.record.breadcrumbs = list;
                getChildren(vm.record).then(function (response) {
                    vm.record_children = response.data;
                    vm.childrenLoading = false;
                })
            }).catch(function(error) {
                Notifications.add('Could not load breadcrumbs!', 'error');
            })
        })
    }

    function getVersionSelectData() {
        vm.currentVersion = vm.record._id;
        vm.record.versions.push(angular.copy(vm.record));
        vm.record.versions.sort(function (a, b) {
            var a_date = new Date(a.create_date),
                b_date = new Date(b.create_date);
            if (a_date < b_date) return -1;
            if (a_date > b_date) return 1;
            return 0;
        })
    }

    vm.expandChildren = function (jqueryobj, e, reload) {
        var tree = vm.recordTreeData;
        var parent = tree.map(function(x) {return getNodeById(x, e.node.original._id); })[0];
        var children = tree.map(function(x) {return getNodeById(x, parent._id); })[0].children;
        if(e.node.children.length < 2 || reload) {
            $http.get(vm.url+"search/"+e.node.original._id+"/children/", {params: {structure: vm.structure, page_size: 10, page: Math.ceil(children.length/10)}}).then(function(response) {
                var count = response.headers('Count');
                children.pop();
                response.data.forEach(function(child) {
                    child = createChild(child);
                    children.push(child);
                    vm.recordTreeInstance.jstree(true).create_node(e.node.id, angular.copy(child));
                });
                if(children.length < count) {
                    children.push({
                        text: $translate.instant("SEE_MORE"),
                        see_more: true,
                        type: "plus",
                        parent: {id: parent._id, index: parent._index},
                        _source: {
                        }
                    });
                    vm.recordTreeInstance.jstree(true).create_node(e.node.id, {
                        text: $translate.instant("SEE_MORE"),
                        see_more: true,
                        type: "plus",
                        parent: {id: parent._id, index: parent._index},
                        _source: {
                        }
                    });
                }
                vm.recordTreeInstance.jstree(true).delete_node(vm.recordTreeInstance.jstree(true).get_node(e.node.id).children[0]);
                parent.state = {opened: true}
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

    vm.getStructureById = function(structures, id) {
        var structure = null;
        structures.forEach(function(x) {
            if(x.id === id) {
                structure = x;
            }
        })
        return structure;
    }

    vm.viewFile = function(file) {
        var params = {};
        if(file.href != "") {
            params.path = file.href+"/"+file.filename;
        } else {
            params.path = file.filename;
        }
        var showFile = $sce.trustAsResourceUrl(appConfig.djangoUrl + "information-packages/"+file.ip+"/files/?path="+params.path);
        $window.open(showFile, '_blank');
    }

    vm.includeDescendants = false;
    vm.emailDocument = function(record) {
        return $http({
            method: 'POST',
            url: appConfig.djangoUrl+'search/' + record._id + '/send-as-email/',
            data: {
                include_descendants: vm.includeDescendants
            }
        }).then(function(response) {
            Notifications.add($translate.instant('EMAIL_SENT'), 'success');
        }).catch(function(response) {
            if(![401, 403, 500, 503].includes(response.status)) {
                if(response.data && response.data.detail) {
                    Notifications.add(response.data.detail, "error");
                } else {
                    Notifications.add($translate('UNKNOWN_ERROR'), 'error')
                }
            }
        })
    }

    vm.gotoSearch = function() {
        $rootScope.$broadcast('CHANGE_TAB', {tab: 0});
        $state.go("home.access.search");
    }

    vm.setCurrentVersion = function(node_id) {
        var node = null;
        vm.record.versions.forEach(function(version) {
            if(version._id == node_id) {
                node = version;
            }
        })
        if(node) {
            return Search.setAsCurrentVersion(node, true).then(function(response){
                vm.loadRecordAndTree(node._index, node._id);
            })
        }
    }

    vm.showVersion = function (node_id) {
        var node = null;
        if (vm.record.versions) {
            vm.record.versions.forEach(function (version) {
                if (version._id == node_id) {
                    node = version;
                }
            })
            var versions = angular.copy(vm.record.versions);
        }
        if (node) {
            vm.selectRecord(null, {node: {original: node},  action: "select_node"});
        }
    }

    vm.addToStructure = function(record) {
        Search.updateNode(record,{parent: vm.tags.descendants.value.id, structure: vm.tags.structure.value.id}, true).then(function(response) {
            $state.reload();
        }).catch(function(response) {
            if(![401, 403, 500, 503].includes(response.status)) {
                if(response.data && response.data.detail) {
                    Notifications.add(response.data.detail, "error");
                } else {
                    Notifications.add($translate('UNKNOWN_ERROR'), 'error')
                }
            }
        })
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
            Notifications.add( "Fältet: " + data.key + ", har ändrats i: " + vm.record.name, "success");
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
            Notifications.add( "Fältet: " + data.key + ", har lagts till i: " + vm.record.name, "success");
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
            Notifications.add( "Fältet: " + field + ", har tagits bort från: " + vm.record.name, "success");
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
            vm.loadRecordAndTree(vm.record._index, vm.record._id);
        }, function () {
            vm.loadRecordAndTree(vm.record._index, vm.record._id);
            $log.info('modal-component dismissed at: ' + new Date());
        });
    }
    vm.addNodeModal = function(node, structure) {
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
                    node: node,
                    structure: structure
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
    vm.newStructureModal = function(node) {
        var modalInstance = $uibModal.open({
            animation: true,
            ariaLabelledBy: 'modal-title',
            ariaDescribedBy: 'modal-body',
            templateUrl: 'static/frontend/views/create_new_structure_modal.html',
            controller: 'StructureModalInstanceCtrl',
            controllerAs: '$ctrl',
            size: "lg",
            resolve: {
                data: {
                    node: node
                }
            }
        });
        modalInstance.result.then(function (data, $ctrl) {
            vm.loadRecordAndTree(node._index, node._id);
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
            vm.recordTreeInstance.jstree(true).delete_node(node.id)
            vm.recordTreeInstance.jstree(true).select_node(node.parent);
        }, function () {
            $log.info('modal-component dismissed at: ' + new Date());
        });
    }
    vm.removeNodeFromStructureModal = function(node, structure) {
        var modalInstance = $uibModal.open({
            animation: true,
            ariaLabelledBy: 'modal-title',
            ariaDescribedBy: 'modal-body',
            templateUrl: 'static/frontend/views/remove_node_from_structure_modal.html',
            controller: 'RemoveNodeModalInstanceCtrl',
            controllerAs: '$ctrl',
            size: "lg",
            resolve: {
                data: {
                    node: node,
                    structure: structure
                }
            }
        });
        modalInstance.result.then(function (data, $ctrl) {
            vm.recordTreeInstance.jstree(true).delete_node(node.id)
            vm.recordTreeInstance.jstree(true).select_node(node.parent);
        }, function () {
            $log.info('modal-component dismissed at: ' + new Date());
        });
    }
    vm.changeOrganizationModal = function(node) {
        var modalInstance = $uibModal.open({
            animation: true,
            ariaLabelledBy: 'modal-title',
            ariaDescribedBy: 'modal-body',
            templateUrl: 'modals/change_node_organization.html',
            controller: 'NodeOrganizationModalInstanceCtrl',
            controllerAs: '$ctrl',
            size: "lg",
            resolve: {
                data: {
                    node: node
                }
            }
        });
        modalInstance.result.then(function (data, $ctrl) {
            vm.loadRecordAndTree(node._index, node._id);
        }, function () {
            $log.info('modal-component dismissed at: ' + new Date());
        });
    }
});
