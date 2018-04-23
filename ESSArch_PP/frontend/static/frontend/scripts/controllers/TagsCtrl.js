angular.module('myApp').controller('TagsCtrl', function($scope, vm, $http, Notifications, appConfig, $state) {
    vm.tags = {
        archive: {
            options: [],
            value: null,
            previous: null
        },
        structure: {
            options: [],
            value: null,
            previous: null
        },
        descendants: {
            options: [],
            value: null,
            previous: null
        }
    }
    vm.resetForm = function () {
        vm.tags = {
            archive: {
                options: [],
                value: null,
                previous: null
            },
            structure: {
                options: [],
                value: null,
                previous: null
            },
            descendants: {
                options: [],
                value: null,
                previous: null
            }
        }
    }

    $scope.tagsPlaceholder = function(type) {
        if ((!$scope.tagsLoading && type.toUpperCase() == "ARCHIVE" && vm.tags.archive.options.length == 0) || (!$scope.structuresLoading && type.toUpperCase() == "CLASSIFICATION_STRUCTURE" && vm.tags.structure.options.length == 0) || (!$scope.descendantsLoading && type.toUpperCase() == "STRUCTURE_UNIT" && vm.tags.descendants.options.length == 0)) {
            if(type) {
                return "NO_"+type.toUpperCase()+"S";
            } else {
                return "NO_TAGS";
            }
        } else {
            if(type) {
                return "SELECT_"+type.toUpperCase()+"_TAG";
            } else {
                return "SELECT_TAGS";
            }
        }
    }

    $scope.getArchives = function (search) {
        return $http({
            method: 'GET',
            url: appConfig.djangoUrl + 'tags/',
            params: {index: 'archive', search: search?search:null}
        }).then(function(response) {
            var mapped = response.data.map(function(item){
                var obj = item.current_version;
                obj.parent_id = item.id;
                obj.structures = item.structures
                return obj;
            });
            vm.tags.archive.options = mapped;
            return mapped;
        }).catch(function(response) {
            Notifications.add(response.data.detail, 'error');
        });
    }

    // Functions for selects when placing unplaced node
    $scope.getStructures = function(archive) {
        $scope.structuresLoading = true;
        var mapped = archive.structures.map(function(item) {
            var obj = item.structure;
            obj.parent_id = item.id;
            return obj;
        })
        $scope.structuresLoading = false;
        vm.tags.structure.options = mapped;
    }

    $scope.getTagDescendants = function(id1, id2, search) {
        $scope.descendantsLoading = true;
        return $http({
            method: 'GET',
            url: appConfig.djangoUrl + 'tags/' + id1 + '/descendants/',
            params: {structure: id2, search: search?search:null, index: 'component'}
        }).then(function(response) {
            var mapped = response.data.map(function(item){
                var obj = item.current_version;
                obj.parent_id = item.id;
                obj.structures = item.structures
                return obj;
            });
            $scope.descendantsLoading = false;
            vm.tags.descendants.options = mapped;
            return mapped;
        })
    }

    $scope.getDescendantId = function() {
        if(vm.tags.structure.value && vm.tags.descendants.value) {
            var id = null;
            vm.tags.descendants.value.structures.forEach(function(item) {
                if(item.structure.id == vm.tags.structure.value.id) {
                    id = item.id;
                }
            })
            return id;
        } else {
            return null;
        }
    }

    $scope.archiveChanged = function(item) {
        if(vm.tags.archive.previous = null || item.id != vm.tags.archive.previous) {
            $scope.getStructures(vm.tags.archive.value);
            vm.tags.structure.value = null;
            vm.tags.archive.previous = item.id;
        }
    }
    $scope.structureChanged = function(item) {
        if(vm.tags.structure.previous == null || item.id != vm.tags.structure.previous) {
            $scope.getTagDescendants(vm.tags.archive.value.parent_id, vm.tags.structure.value.id);
            vm.tags.descendants.value = null;
            vm.tags.structure.previous = item.id;
        }
    }
})