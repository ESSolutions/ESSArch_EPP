angular.module('myApp').controller('SearchCtrl', function(Search, $q, $scope, $http, $rootScope, appConfig, $log, $timeout, TopAlert, $sce, $translate, $anchorScroll, $uibModal) {
    var vm = this;
    $scope.angular = angular;
    vm.url = appConfig.djangoUrl;

    vm.currentItem = null;
    vm.displayed = null;
    vm.viewResult = false;
    vm.numberOfResults = 0;
    vm.resultsPerPage = 25;

    var auth = window.btoa("user:user");
    var headers = { "Authorization": "Basic " + auth };

    vm.filterObject = {
        q: "",
        type: null
    }
    vm.calculatePageNumber = function() {
        if(!angular.isUndefined(vm.tableState) && vm.tableState.pagination) {
            var pageNumber = vm.tableState.pagination.start/vm.tableState.pagination.number;
            var firstResult = pageNumber*vm.tableState.pagination.number+1;
            var lastResult = vm.searchResult.length+((vm.tableState.pagination.start/vm.tableState.pagination.number)*vm.tableState.pagination.number);
            var total = vm.numberOfResults;
            return $translate.instant("SHOWING_RESULT") + " " + firstResult + "-"+ lastResult + " " + $translate.instant("OF") + " " + total;
        }
    }
    vm.resultNumber = function(index) {
        if(vm.tableState.pagination) {
            return index+1+((vm.tableState.pagination.start/vm.tableState.pagination.number)*vm.tableState.pagination.number);
        }
    }
    vm.searchSubmit = function(searchString) {
        vm.filterObject.q = searchString;
        if(vm.tableState) {
            vm.tableState.pagination.start = 0;
        }
        vm.search(vm.tableState);
        vm.activeTab = 0;
    }

    /**
     * Pipe function for search results
     */
    vm.search = function(tableState) {
        if (tableState) {
            vm.searching = true;
            vm.tableState = tableState
            var pagination = tableState.pagination;
            var start = pagination.start || 0;     // This is NOT the page number, but the index of item in the list that you want to use to display the table.
            var number = pagination.number;  // Number of entries showed per page.
            var pageNumber = start / number + 1;
            Search.query(vm.filterObject, pageNumber, number).then(function (response) {
                angular.copy(response.data, vm.searchResult);
                vm.numberOfResults = response.count;
                tableState.pagination.numberOfPages = response.numberOfPages;//set the number of pages so the pagination can update
                vm.searching = false;
                vm.loadTags(response.aggregations);
            })
        } else {
            vm.showResults = true;
        }
    }
    vm.tags = [];
    vm.loadTags = function(aggregations) {
        var tags = [];
        var typeMissing = true;
        var children = aggregations._filter_type.type.buckets.map(function(item) {
            item.text = item.key + " (" + item.doc_count + ")";
            item.state = {opened: true, selected: vm.filterObject.type==item.key?true:false}
            item.type = item.key;
            if(item.key == vm.filterObject.type) {
                typeMissing = false;
            }
            item.children = [];
            return item;
        });
        if(vm.filterObject.type && typeMissing) {
            children.push({
                key: vm.filterObject.type,
                text: vm.filterObject.type+"(0)",
                state: {opened: true, selected: true},
                type: vm.filterObject.type,
                children: []
            });
        }
        var rootTag = {
            text: "Arkiv",
            parent: "#",
            type: "archive",
            state: {opened: true, disabled: true},
            children: [ {
                text: "Typ" + " (" + aggregations._filter_type.doc_count + ")",
                state: {opened: true, disabled: true},
                type: 'series',
                children: children,
            }]
        };
        tags = [rootTag];
        vm.recreateFilterTree(tags)
    }

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

    vm.openResult = function(result) {
        if(!result.id && result._id) {
            result.id = result._id;
        }
        vm.viewContent = true;
        $http.get(vm.url+"search/"+result.id+"/", {headers: headers}).then(function(response) {
            vm.record = response.data;
            vm.activeTab = 1;
            if(response.data.parents) {
                vm.buildRecordTree(response.data).then(function(node) {
                    var treeData = [node];
                    vm.recreateRecordTree(treeData);
                })
            } else {
                if(angular.isUndefined(response.data.name)) {
                    response.data.name = "";
                }
                response.data.text = "<b>" + response.data.reference_code + "</b> " + response.data.name;
                response.data.type = response.data._type;
                var treeData = [response.data];
                vm.recreateRecordTree(treeData);
            }
            vm.record.children = [{text: "", parent: vm.record.id, placeholder: true, icon: false, state: {disabled: true}}];
            getChildren(vm.record).then(function(response) {
                vm.record_children = response.data;
            })
        });
    }
    vm.treeIds = ["tree_id1", "Allänna arkivschemat"]
    vm.treeId = "tree_id1";
    vm.buildRecordTree = function(startNode) {
        if(angular.isUndefined(startNode.name)) {
            startNode.name = "";
        }
        startNode.text = "<b>" + startNode.reference_code + "</b> " + startNode.name;
        startNode.type = startNode._type;
        startNode.state = {opened: true};
        if(startNode._id == vm.record._id) {
            startNode.state.selected = true;
        }
        if(startNode.parents) {
            return $http.get(vm.url+"search/"+startNode.parents[vm.treeId]+"/", {headers: headers}).then(function(response) {
                var p = response.data;
                p.children = [];
                return getChildren(p).then(function(children) {
                    children.data.forEach(function(child) {
                        if(child._id == startNode._id) {
                            p.children.push(startNode);
                        } else {
                            if(angular.isUndefined(child._source.name)) {
                                child._source.name = "";
                            }
                            child._source.text = "<b>" + child._source.reference_code + "</b> " + child._source.name;
                            child._source.type = child._type;
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
        return $http.get(vm.url+"search/"+node._id+"/children/", {headers: headers, params: {tree_id: vm.treeId, page_size: 10, page: 1}}).then(function(response) {
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
    vm.searchResult = [];
    vm.treeConfig = {
        core : {
            multiple : false,
            animation: 50,
            error : function(error) {
                $log.error('treeCtrl: error from js tree - ' + angular.toJson(error));
            },
            check_callback : true,
            worker : true,
            themes: {
                name: "default",
                icons: false
            }
        },
        version : 1,
        plugins : []
    };
    /**
     * Recreates filter tree with given tags.
     * Version variable is updated so that the tree will detect
     * a change in the configuration object, desroy and rebuild with data from vm.tags
     */
    vm.recreateFilterTree = function(tags) {
        vm.ignoreChanges = true;
        angular.copy(tags, vm.tags);
        vm.treeConfig.version++;
    }

    vm.selectFilter = function(jqueryobj, e) {
        if(e.action == "select_node") {
            if(vm.filterObject.type == e.node.original.key) {
                vm.treeInstance.jstree(true).deselect_node(e.node);
                vm.filterObject.type = null;
                if(vm.tableState) {
                    vm.tableState.pagination.start = 0;
                }
                vm.search(vm.tableState);
            } else {
                vm.filterObject.type = e.node.original.key;
                if(vm.tableState) {
                    vm.tableState.pagination.start = 0;
                }
                vm.search(vm.tableState);
            }
        }
    }

    vm.applyModelChanges = function() {
        return !vm.ignoreChanges;
    };
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
            },
            archive : {
                icon : 'fa fa-archive'
            },
            series : {
                icon : 'fa fa-file-o'
            },
            volume: {
                icon: 'fa fa-hdd-o'
            },
            plus: {
                icon: "fa fa-plus"
            }
        },
        version : 1,
        plugins : ['types']
    };
    vm.recordTreeData = [];
    vm.selectRecord = function (jqueryobj, e) {
        if(e.node && e.node.original.see_more) {
            var tree = vm.recordTreeData;
            var parent = vm.recordTreeInstance.jstree(true).get_node(e.node.parents[0]);
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
                    if(angular.isUndefined(child._source.name)) {
                        child._source.name = "";
                    }
                    child._source.text = "<b>" + child._source.reference_code + "</b> " + child._source.name;
                    child._source.type = child._type;
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
                    if(angular.isUndefined(child._source.name)) {
                        child._source.name = "";
                    }
                    child._source.text = "<b>" + child._source.reference_code + "</b> " + child._source.name;
                    child._source.type = child._type;
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
    vm.viewFile = function(record) {
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
});
