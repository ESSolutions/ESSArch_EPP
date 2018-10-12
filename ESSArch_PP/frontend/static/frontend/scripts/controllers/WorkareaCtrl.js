angular.module('essarch.controllers').controller('WorkareaCtrl', function (vm, ipSortString, WorkareaFiles, Workarea, $scope, $controller, $rootScope, Resource, $interval, $timeout, appConfig, $cookies, $anchorScroll, $translate, $state, $http, listViewService, Requests, $uibModal, $sce, $window, ContextMenuBase) {
    $controller('BaseCtrl', { $scope: $scope, vm: vm, ipSortString: ipSortString });

    vm.browserstate = {
        path: ""
    };
    vm.organizationMember = {
        current: null,
        options: [],
    }
    vm.$onInit = function() {
        vm.organizationMember.current = $rootScope.auth;
        if($scope.checkPermission('ip.see_all_in_workspaces') && $rootScope.auth.current_organization) {
            $http.get(appConfig.djangoUrl+"organizations/"+$rootScope.auth.current_organization.id+"/").then(function(response) {
                vm.organizationMember.options = response.data.group_members;
            })
        }
    }
    vm.archived = null;
    $scope.menuOptions = function (rowType, row) {
        return [
            ContextMenuBase.changeOrganization(
                function () {
                    $scope.ip = row;
                    $rootScope.ip = row;
                    vm.changeOrganizationModal($scope.ip);
            })
        ];
    }

    vm.callServer = function callServer(tableState) {
        $scope.ipLoading = true;
        if(vm.displayedIps.length == 0) {
            $scope.initLoad = true;
        }
        if(!angular.isUndefined(tableState)) {
            $scope.tableState = tableState;
            var search = "";
            if(tableState.search.predicateObject) {
                var search = tableState.search.predicateObject["$"];
            }
            var sorting = tableState.sort;
            var pagination = tableState.pagination;
            var start = pagination.start || 0;     // This is NOT the page number, but the index of item in the list that you want to use to display the table.
            var number = pagination.number || vm.itemsPerPage;  // Number of entries showed per page.
            var pageNumber = start/number+1;
            Resource.getWorkareaIps(vm.workarea, start, number, pageNumber, tableState, sorting, search, $scope.expandedAics, $scope.columnFilters, vm.organizationMember.current).then(function (result) {
                vm.displayedIps = result.data;
                tableState.pagination.numberOfPages = result.numberOfPages;//set the number of pages so the pagination can update
                $scope.ipLoading = false;
                $scope.initLoad = false;
                ipExists();
            }).catch(function(response) {
                if(response.status == 404) {
                    var filters = angular.extend({
                        state: ipSortString
                    }, $scope.columnFilters)

                    if(vm.workarea) {
                        filters.workarea = vm.workarea;
                    }

                    listViewService.checkPages("workspace", number, filters).then(function (result) {
                        tableState.pagination.numberOfPages = result.numberOfPages;//set the number of pages so the pagination can update
                        tableState.pagination.start = (result.numberOfPages*number) - number;
                        vm.callServer(tableState);
                    });
                }
            });
        }
    };

    function ipExists() {
        if($scope.ip != null) {
            var temp = false;
            vm.displayedIps.forEach(function(aic) {
                if($scope.ip.id == aic.id) {
                    temp = true;
                } else {
                    aic.information_packages.forEach(function(ip) {
                        if($scope.ip.id == ip.id) {
                            temp = true;
                        }
                    })
                }
            })
            if(!temp) {
                $scope.eventShow = false;
                $scope.statusShow = false;
                $scope.filebrowser = false;
                $scope.requestForm = false;
                $scope.eventlog = false;
                $scope.requestEventlog = false;
            }
        }
    }
    // Remove ip
    $scope.ipRemoved = function (ipObject) {
        $scope.edit = false;
        $scope.select = false;
        $scope.eventlog = false;
        $scope.eventShow = false;
        $scope.statusShow = false;
        $scope.filebrowser = false;
        $scope.requestForm = false;
        if (vm.displayedIps.length == 0) {
            $state.reload();
        }
        $scope.getListViewData();
    }

    //Click function for Ip table
    $scope.ipTableClick = function (row) {
        if (row.workarea && row.workarea[0].read_only) {
            $scope.ip = row;
            $rootScope.ip = row;
            $scope.select = false;
            $scope.eventlog = false;
            $scope.edit = false;
            $scope.eventShow = false;
            $scope.requestForm = false;
            $scope.filebrowser = false;
            return;
        }
        if (row.package_type == 1 || row.workarea == null) {
            $scope.select = false;
            $scope.eventlog = false;
            $scope.edit = false;
            $scope.eventShow = false;
            $scope.requestForm = false;
            $scope.initRequestData();
            if ($scope.ip != null && $scope.ip.object_identifier_value == row.object_identifier_value) {
                $scope.ip = null;
                $rootScope.ip = null;
                $scope.filebrowser = false;
            } else {
                $scope.ip = row;
                $rootScope.ip = $scope.ip;
            }
            return;
        }
        if ($scope.select && $scope.ip.object_identifier_value == row.object_identifier_value) {
            $scope.select = false;
            $scope.eventlog = false;
            $scope.edit = false;
            $scope.eventShow = false;
            $scope.requestForm = false;
            $scope.ip = null;
            $rootScope.ip = null;
            $scope.filebrowser = false;
            $scope.initRequestData();
        } else {
            $scope.select = true;
            $scope.eventlog = true;
            $scope.edit = true;
            $scope.requestForm = true;
            $scope.eventShow = false;
            $scope.ip = row;
            $rootScope.ip = $scope.ip;
        }
        $scope.statusShow = false;
    };

    $scope.filebrowserClick = function (ip) {
        if ($scope.filebrowser && $scope.ip == ip) {
            $scope.filebrowser = false;
            if(!$scope.select && !$scope.edit && !$scope.statusShow && !$scope.eventShow && !$scope.requestForm && !$scope.filebrowser) {
                $scope.ip = null;
                $rootScope.ip = null;
            }
        } else {
            $scope.ip = ip;
            $rootScope.ip = ip;
            $scope.previousGridArrays = [];
            $scope.filebrowser = true;
            if(!$rootScope.flowObjects[$scope.ip.id]) {
                $scope.createNewFlow($scope.ip);
            }
            $scope.currentFlowObject = $rootScope.flowObjects[$scope.ip.id];
            if($scope.filebrowser) {
                $scope.showFileUpload = false;
                $timeout(function() {
                    $scope.showFileUpload = true;
                });
            }
            $scope.previousGridArrays = [];
        }
    }

    // **********************************
    //            Upload
    // **********************************

    $scope.updateGridArray = function (ip) {
        $scope.$broadcast("UPDATE_FILEBROWSER", {});
    };

    $scope.uploadDisabled = false;
    $scope.updateListViewTimeout = function(timeout) {
        $timeout(function(){
            $scope.getListViewData();
        }, timeout);
    };

    vm.flowDestination = null;
    $scope.showFileUpload = true;
    $scope.currentFlowObject = null;
    $scope.getFlowTarget = function() {
        return appConfig.djangoUrl + 'workarea-files/upload/?type=' + vm.workarea + '/';
    };
    $scope.getQuery = function(FlowFile, FlowChunk, isTest) {
        return {destination: vm.browserstate.path};
    };
    $scope.fileUploadSuccess = function(ip, file, message, flow) {
        $scope.uploadedFiles ++;
        var path = flow.opts.query.destination + file.relativePath;

        WorkareaFiles.mergeChunks({
            type: vm.workarea,
        }, { path: path });
    };
    $scope.fileTransferFilter = function(file)
    {
        return file.isUploading();
    };
    $scope.removeFiles = function() {
        $scope.selectedCards.forEach(function(file) {
            listViewService.deleteWorkareaFile(vm.workarea, vm.browserstate.path, file)
            .then(function () {
                $scope.updateGridArray();
            });
        });
        $scope.selectedCards = [];
    }
    $scope.isSelected = function (card) {
        var cardClass = "";
        $scope.selectedCards.forEach(function (file) {
            if (card.name == file.name) {
                cardClass = "card-selected";
            }
        });
        return cardClass;
    };
    $scope.resetUploadedFiles = function() {
        $scope.uploadedFiles = 0;
    }
    $scope.uploadedFiles = 0;
    $scope.flowCompleted = false;
    $scope.flowComplete = function(flow, transfers) {
        if(flow.progress() === 1) {
            flow.flowCompleted = true;
            flow.flowSize = flow.getSize();
            flow.flowFiles = transfers.length;
            flow.cancel();
            if(flow == $scope.currentFlowObject){
                $scope.resetUploadedFiles();
            }
        }

        $scope.updateGridArray();
    }
    $scope.hideFlowCompleted = function(flow) {
        flow.flowCompleted = false;
    }
    $scope.getUploadedPercentage = function(totalSize, uploadedSize, totalFiles) {
        if(totalSize == 0 || uploadedSize/totalSize == 1) {
            return ($scope.uploadedFiles / totalFiles) * 100;
        } else {
            return (uploadedSize / totalSize) * 100;
        }
    }

    $scope.createNewFlow = function(ip) {
        var flowObj = new Flow({
            target: appConfig.djangoUrl+'workarea-files/upload/?type=' + vm.workarea,
            simultaneousUploads: 15,
            maxChunkRetries: 5,
            chunkRetryInterval: 1000,
            headers: {'X-CSRFToken' : $cookies.get("csrftoken")},
            complete: $scope.flowComplete
        });
        flowObj.on('complete', function(){
            $scope.flowComplete(flowObj, flowObj.files);
        });
        flowObj.on('fileSuccess', function(file,message){
            $scope.fileUploadSuccess(ip, file, message, flowObj);
        });
        flowObj.on('uploadStart', function(){
            flowObj.opts.query = {destination: vm.browserstate.path};
        });
        $rootScope.flowObjects[ip.id] = flowObj;
    }
});
