angular.module('myApp').controller('SearchDetailCtrl', function($scope, $stateParams,Search, $q, $scope, $http, $rootScope, appConfig, $log, $timeout, TopAlert, $sce, $translate, $anchorScroll, $uibModal, PermPermissionStore, $window, $state) {
    var vm = this;
    $scope.angular = angular;
    vm.url = appConfig.djangoUrl;
    var auth = window.btoa("user:user");
    var headers = { "Authorization": "Basic " + auth };
    vm.$onInit = function() {
        vm.item = {
            id: $stateParams.id,
        }
        vm.viewContent = true;
        $http.get(vm.url+"search/"+vm.item.id+"/", {headers: headers}).then(function(response) {
            vm.record = response.data;
            vm.activeTab = 1;
            if(response.data.parent) {
                vm.buildRecordTree(response.data).then(function(node) {
                    var treeData = [node];
                    vm.recreateRecordTree(treeData);
                })
            } else {
                if(angular.isUndefined(response.data.title)) {
                    response.data.title = "";
                }
                response.data.text = "<b>" + (response.data.reference_code ? response.data.reference_code : "") + "</b> " + response.data.title;
                var treeData = [response.data];
                vm.recreateRecordTree(treeData);
            }
            vm.record.children = [{text: "", parent: vm.record.id, placeholder: true, icon: false, state: {disabled: true}}];
            vm.record.state.opened = false;
            if(angular.isUndefined(vm.record.terms_and_condition)) {
                vm.record.terms_and_condition = null;
            }
            getChildren(vm.record).then(function(response) {
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
        return $http.get(vm.url+"search/"+tag.id+"/").then(function(response) {
            return response.data;
        });
    }

    vm.treeIds = ["Allmänna arkivschemat", "Verksamhetsbaserad"]
    vm.treeId = "Allmänna arkivschemat";
    vm.buildRecordTree = function(startNode) {
        if(angular.isUndefined(startNode.title)) {
            startNode.title = "";
        }
        startNode.text = "<b>" + (startNode.reference_code ? startNode.reference_code : "") + "</b> " + startNode.title;
        startNode.state = {opened: true};
        if(startNode._id == vm.record._id) {
            startNode.state.selected = true;
        }
        if(startNode.parent) {
            return $http.get(vm.url+"search/"+startNode.parent+"/", {headers: headers}).then(function(response) {
                var p = response.data;
                p.children = [];
                return getChildren(p).then(function(children) {
                    children.data.forEach(function(child) {
                        if(child._id == startNode._id) {
                            p.children.push(startNode);
                        } else {
                            if(angular.isUndefined(child._source.title)) {
                                child._source.title = "";
                            }
                            child._source._index = child._index;
                            child._source.text = "<b>" + (child._source.reference_code ? child._source.reference_code : "") + "</b> " + child._source.title;
                            child._source.state = {opened: true};
                            if(!child._source.children) {
                                child._source.children = [{text: "", parent: child._id, placeholder: true, icon: false, state: {disabled: true}}];
                            }
                            child._source.state = { opened: false };
                            child._source._id = child._id;
                            p.children.push(child._source);
                        }
                    });
                    if(children.data.length < children.count) {
                        p.children.push({
                            text: $translate.instant("SEE_MORE"),
                            see_more: true,
                            type: "plus",
                            parent: p._id,
                        });
                        if(!getNodeById(p, startNode._id)) {
                            startNode.state.opened = false;
                            p.children.push(startNode);
                        }
                    }
                    return vm.buildRecordTree(p);
                })
            });
        } else {
            return startNode;
        }
    }
    function getChildren(node) {
        if(!node._id && node.id) {
            node._id = node.id;
        }
        return $http.get(vm.url+"search/"+node._id+"/children/", {headers: headers, params: {page_size: 10, page: 1}}).then(function(response) {
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
        version : 1,
        contextmenu: {
            items: function (o, cb) {
                var archiveManagement = {
                    label: "Arkivvård",
                    submenu: {
                        appraisal: {
                            label: "Gallring",
                            action: function (o) {
                                vm.appraisal(vm.record);
                            },
                        }
                    }
                };
                var actions = { archiveManagement: archiveManagement };
                cb(actions);
                return actions;
            }
        },
        plugins : ['types', 'contextmenu']
    };

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
            $http.get(vm.url+"search/"+e.node.original.parent+"/children/", {headers: headers, params: {tree_id: vm.treeId, page_size: 10, page: Math.ceil(children.length/10)}}).then(function(response) {
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
                    if(angular.isUndefined(child._source.title)) {
                        child._source.title = "";
                    }
                    child._source.text = "<b>" + (child._source.reference_code ? child._source.reference_code : "") + "</b> " + child._source.title;
                    if(!child._source.children) {
                        child._source.children = [{text: "", parent: child._id, icon: false, placeholder: true, state: {disabled: true}}];
                    }
                    child._source.state = { opened: false };
                    child._source._id = child._id;
                    children.push(child._source);
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
            $state.go(".", {id: vm.record._id}, {notify: false});
            if(angular.isUndefined(vm.record.terms_and_condition)) {
                vm.record.terms_and_condition = null;
            }
            vm.record.children = [{text: "", parent: vm.record.id, placeholder: true, icon: false, state: {disabled: true}}];
            getChildren(vm.record).then(function(response) {
                vm.record_children = response.data;
            })
        }
    }

    vm.expandChildren = function (jqueryobj, e) {
        var tree = vm.recordTreeData;
        var parent = tree.map(function(x) {return getNodeById(x, e.node.original._id); })[0];
        var children = tree.map(function(x) {return getNodeById(x, parent._id); })[0].children;
        if(e.node.children.length < 2) {
            $http.get(vm.url+"search/"+e.node.original._id+"/children/", {headers: headers, params: {tree_id: vm.treeId, page_size: 10, page: Math.ceil(children.length/10)}}).then(function(response) {
                var count = response.headers('Count');
                children.pop();
                response.data.forEach(function(child) {
                    if(angular.isUndefined(child._source.title)) {
                        child._source.title = "";
                    }
                    child._source.text = "<b>" + (child._source.reference_code ? child._source.reference_code : "") + "</b> " + child._source.title;
                    if(!child._source.children) {
                        child._source.children = [{text: "", parent: child._id, placeholder: true, icon: false, state: {disabled: true}}];
                    }
                    child._source.state = { opened: false };
                    child._source._id = child._id;
                    child._source.id = child._id;
                    children.push(child._source);
                });
                if(children.length < count) {
                    children.push({
                        text: $translate.instant("SEE_MORE"),
                        see_more: true,
                        type: "plus",
                        parent: parent._id,
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
    vm.viewFile = function(name) {
        var file = $sce.trustAsResourceUrl("/static/frontend/"+name);
        $window.open(file, '_blank');
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
            TopAlert.add( "Fältet: " + data.key + ", har ändrats i: " + vm.record.title, "success");
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
            TopAlert.add( "Fältet: " + data.key + ", har lagts till i: " + vm.record.title, "success");
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
            TopAlert.add( "Fältet: " + field + ", har tagits bort från: " + vm.record.title, "success");
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

    vm.appraisal = function(record) {
        var modalInstance = $uibModal.open({
            animation: true,
            ariaLabelledBy: 'modal-title',
            ariaDescribedBy: 'modal-body',
            templateUrl: 'static/frontend/views/search_appraisal_modal.html',
            controller: 'AppraisalModalInstanceCtrl',
            controllerAs: '$ctrl',
            size: "lg",
            resolve: {
                data: {
                    record: record
                }
            }
        });
        modalInstance.result.then(function (data, $ctrl) {
        }, function () {
            $log.info('modal-component dismissed at: ' + new Date());
        });
    }
});
