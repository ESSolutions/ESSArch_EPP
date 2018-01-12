angular.module('myApp').controller('SearchCtrl', function(Search, $q, $scope, $http, $rootScope, appConfig, $log, $timeout, TopAlert, $sce, $translate, $anchorScroll, $uibModal, PermPermissionStore, $window, $state) {
    var vm = this;
    $scope.angular = angular;
    vm.url = appConfig.djangoUrl;

    vm.currentItem = null;
    vm.displayed = null;
    vm.viewResult = true;
    vm.numberOfResults = 0;
    vm.resultsPerPage = 25;

    var auth = window.btoa("user:user");
    var headers = { "Authorization": "Basic " + auth };

    vm.$onInit = function() {
        if($state.is('home.search.detail')) {
            vm.activeTab = 1;
            vm.showResults = true;
        }
    }

    $scope.checkPermission = function(permissionName) {
        return !angular.isUndefined(PermPermissionStore.getPermissionDefinition(permissionName));
    };
    vm.filterObject = {
        q: "",
        type: null
    }
    vm.changeClassificationStructure = function() {
        vm.searchSubmit(vm.filterObject.q);
        vm.openResult(vm.record);
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

    var getAggregationChildren = function(aggregations, aggrType){
        var aggregation = aggregations['_filter_' + aggrType][aggrType]
        var missing = true;
        children = aggregation.buckets.map(function(item) {
            if (item.title) {
                item.text = item.title + " (" + item.doc_count + ")";
            } else {
                item.text = item.key + " (" + item.doc_count + ")";
            }
            item.state = {opened: true, selected: vm.filterObject[aggrType]==item.key?true:false}
            item.type = item.key;
            if(item.key == vm.filterObject[aggrType]) {
                missing = false;
            }
            item.children = [];
            return item;
        });

        if (vm.filterObject[aggrType] && missing) {
            children.push({
                key: vm.filterObject[aggrType],
                text: vm.filterObject[aggrType] + " (0)",
                state: {opened: true, selected: true},
                type: vm.filterObject[aggrType],
                children: []
            });
        }

        return children;
    }

    vm.loadTags = function(aggregations) {
        var typeChildren = getAggregationChildren(aggregations, 'type');
        var archiveChildren = getAggregationChildren(aggregations, 'archive');
        var institutionChildren = getAggregationChildren(aggregations, 'institution');
        var filters = [
            {
                text: "Typ",
                state: {opened: true, disabled: true},
                type: 'series',
                children: typeChildren,
                branch: 'type',
            },
            {
                text: "Arkiv",
                state: {opened: true, disabled: true},
                children: archiveChildren,
                branch: 'archive',
            },
            {
                text: "Arkivinstitution",
                state: {opened: true, disabled: true},
                children: institutionChildren,
                branch: 'institution',
            },
        ];
        vm.recreateFilterTree(filters)
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
        $state.go("home.search.detail", {id: result.id});
        vm.activeTab = 1;
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
            var parent = vm.treeInstance.jstree(true).get_node(e.node.parent);
            var branch = parent.original.branch;
            if(vm.filterObject[branch] == e.node.original.key) {
                vm.treeInstance.jstree(true).deselect_node(e.node);
                vm.filterObject[branch] = null;
                if(vm.tableState) {
                    vm.tableState.pagination.start = 0;
                }
                vm.search(vm.tableState);
            } else {
                vm.filterObject[branch] = e.node.original.key;
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
});
