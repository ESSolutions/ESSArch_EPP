angular.module('myApp').controller('SearchCtrl', function(Search, $q, $scope, $http, $rootScope, appConfig, $log, $timeout, TopAlert, $sce, $translate, $anchorScroll) {
    var vm = this;

    vm.url = appConfig.djangoUrl;
    //vm.url = "http://192.168.6.105:8002/api/";

    vm.currentItem = null;
    vm.displayed = null;
    vm.viewResult = false;
    vm.numberOfResults = 0;
    vm.resultsPerPage = 25;
    var watchers = [];
    watchers.push($rootScope.$watch(function(){return $rootScope.selectedTag}, function(newVal, oldVal) {
        vm.currentItem = newVal;
        if(oldVal) {
            vm.search(vm.searchString);
        }
    }));
    var auth = window.btoa("user:user");
    var headers = { "Authorization": "Basic " + auth };
    $rootScope.$on('$stateChangeStart', function() {
        watchers.forEach(function(watcher) {
            watcher();
        });
    });

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
            $anchorScroll();
            if(response.data.parents) {
                vm.buildRecordTree(response.data).then(function(node) {
                    var treeData = [node];
                    vm.recreateRecordTree(treeData);
                })
            } else {
                response.data.text = response.data.name;
                response.data.type = response.data._type;
                var treeData = [response.data];
                vm.recreateRecordTree(treeData);
            }
        });
    }
    vm.treeIds = ["tree_id1", "Allänna arkivschemat"]
    vm.treeId = "tree_id1";
    vm.buildRecordTree = function(startNode) {
        startNode.text = startNode.name;
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
                            child._source.text = child._source.name;
                            child._source.type = child._type;
                            child._source.state = {opened: true};
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
                    }
                    return vm.buildRecordTree(p);
                })
            });
        } else {
            return startNode;
        }
    }
    function getChildren(node) {
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
        if(e.node.original.see_more) {
            var tree = vm.recordTreeData;
            var parent = vm.recordTreeInstance.jstree(true).get_node(e.node.parents[0]);
            var children = tree[tree.map(function(x) {return x._id; }).indexOf(parent.original._id)].children;
            $http.get(vm.url+"search/"+e.node.original.parent+"/children/", {headers: headers, params: {tree_id: vm.treeId, page_size: 10, page: Math.ceil(children.length/10)}}).then(function(response) {
                var count = response.headers('Count');
                var see_more = children.pop()
                response.data.forEach(function(child) {
                    child._source.text = child._source.name;
                    child._source.type = child._type;
                    child._source.state = {opened: true};
                    children.push(child._source);
                });
                if(children.length < count) {
                    children.push(see_more);
                }
                vm.recreateRecordTree(tree);
            });
            return;
        }
        if (e.action == "select_node") {
            vm.record = e.node.original;
        }
    }
});
