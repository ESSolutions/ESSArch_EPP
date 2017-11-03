angular.module('myApp').controller('WorkareaCtrl', function (vm, ipSortString, WorkareaFiles, Workarea, $scope, $controller, $rootScope, Resource, $interval, $timeout, appConfig, $cookies, $anchorScroll, $translate, $state, $http, listViewService, Requests, $uibModal, $sce, $window) {
    $controller('BaseCtrl', { $scope: $scope, vm: vm, ipSortString: ipSortString });

    vm.archived = null;
    $scope.menuOptions = function () {
        return [];
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
            Resource.getWorkareaIps(vm.workarea, start, number, pageNumber, tableState, sorting, search, $scope.expandedAics, $scope.columnFilters).then(function (result) {
                vm.displayedIps = result.data;
                tableState.pagination.numberOfPages = result.numberOfPages;//set the number of pages so the pagination can update
                $scope.ipLoading = false;
                $scope.initLoad = false;
                ipExists();
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
    $scope.removeIp = function (ipObject) {
        if(ipObject.package_type == 1) {
            ipObject.information_packages.forEach(function(ip) {
                $scope.removeIp(ip);
            });
        } else {
            $http.delete(appConfig.djangoUrl + "workarea-entries/" + ipObject.workarea.id + "/")
                .then(function () {
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
                });
        }
    }

    //Click function for Ip table
    $scope.ipTableClick = function (row) {
        if (row.workarea.read_only) {
            return;
        }
        if (row.package_type == 1) {
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
            if ($rootScope.auth.id == ip.workarea.user.id || !ip.workarea.user) {
                $scope.ip = ip;
                $rootScope.ip = ip;
                $scope.previousGridArrays = [];
                $scope.filebrowser = true;
                $scope.deckGridInit($scope.ip);
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
    }

    // ***********************
    //       FILEBROWSER
    // ***********************

    $scope.previousGridArrays = [];
    $scope.ip = $rootScope.ip;
    $scope.listView = false;
    $scope.gridView = true;
    $scope.useListView = function() {
        $scope.filesPerPage = $cookies.get("files-per-page") || 50;
        $scope.listView = true;
        $scope.gridView = false;
    }

    $scope.useGridView = function() {
        $scope.filesPerPage = $cookies.get("files-per-page") || 50;
        $scope.listView = false;
        $scope.gridView = true;
    }

    $scope.filesPerPage = $cookies.get("files-per-page") || 50;
    $scope.changeFilesPerPage = function(filesPerPage) {
        $cookies.put("files-per-page", filesPerPage, { expires: new Date("Fri, 31 Dec 9999 23:59:59 GMT") });
    }
    $scope.previousGridArraysString = function () {
        var retString = $scope.ip.object_identifier_value;

        if ($scope.ip.workarea.packaged && !$scope.ip.workarea.extracted) {
            retString += '.tar';
        }
        retString += '/'

        $scope.previousGridArrays.forEach(function (card) {
            retString = retString.concat(card.name, "/");
        });
        return retString;
    }
    $scope.deckGridData = [];
    $scope.dirPipe = function(tableState) {
        $scope.gridArrayLoading = true;
        if ($scope.deckGridData.length == 0) {
            $scope.initLoad = true;
        }
        if (!angular.isUndefined(tableState)) {
            $scope.tableState = tableState;
            var pagination = tableState.pagination;
            var start = pagination.start || 0;     // This is NOT the page number, but the index of item in the list that you want to use to display the table.
            var number = pagination.number;  // Number of entries showed per page.
            var pageNumber = start / number + 1;
            listViewService.getWorkareaDir(vm.workarea, $scope.previousGridArraysString(), pageNumber, number).then(function(dir) {
                $scope.deckGridData = dir.data;
                tableState.pagination.numberOfPages = dir.numberOfPages;//set the number of pages so the pagination can update
                $scope.gridArrayLoading = false;
                $scope.initLoad = false;
            })
        }
    }
    $scope.deckGridInit = function (ip) {
        $scope.previousGridArrays = [];
        if($scope.tableState) {
            $scope.dirPipe($scope.tableState);
            $scope.selectedCards = [];
        }
    };

    $scope.previousGridArray = function () {
        $scope.previousGridArrays.pop();
        if($scope.tableState) {
            $scope.dirPipe($scope.tableState);
            $scope.selectedCards = [];
        }
    };
    $scope.gridArrayLoading = false;
    $scope.updateGridArray = function (ip) {
        if($scope.tableState) {
            $scope.dirPipe($scope.tableState);
        }
    };
    $scope.expandFile = function (ip, card) {
        if (card.type == "dir" || card.name.endsWith('.tar') || card.name.endsWith('.zip')) {
            $scope.previousGridArrays.push(card);
            if($scope.tableState) {
                $scope.tableState.pagination.start = 0;
                $scope.dirPipe($scope.tableState);
                $scope.selectedCards = [];
            }
        } else {
            $scope.getFile(card);
        }
    };
    $scope.selectedCards = [];
    $scope.cardSelect = function (card) {

        if (includesWithProperty($scope.selectedCards, "name", card.name)) {
            $scope.selectedCards.splice($scope.selectedCards.indexOf(card), 1);
        } else {
            $scope.selectedCards.push(card);
        }
    };

    function includesWithProperty(array, property, value) {
        for (i = 0; i < array.length; i++) {
            if (array[i][property] === value) {
                return true;
            }
        }
        return false;
    }

    $scope.createFolder = function (folderName) {
        var folder = {
            "type": "dir",
            "name": folderName
        };
        var fileExists = false;
        $scope.deckGridData.forEach(function (chosen, index) {
            if (chosen.name === folder.name) {
                fileExists = true;
                folderNameExistsModal(index, folder, chosen);
            }
        });
        if (!fileExists) {
            listViewService.addNewWorkareaFolder(vm.workarea, $scope.previousGridArraysString(), folder)
                .then(function (response) {
                    $scope.updateGridArray();
                });
        }
    }

    $scope.getFile = function (file) {
        file.content = $sce.trustAsResourceUrl(appConfig.djangoUrl + "workarea-files/?type=" + vm.workarea + "&path=" + $scope.previousGridArraysString() + file.name);
        $window.open(file.content, '_blank');
    }
    function folderNameExistsModal(index, folder, fileToOverwrite) {
        var modalInstance = $uibModal.open({
            animation: true,
            ariaLabelledBy: 'modal-title',
            ariaDescribedBy: 'modal-body',
            templateUrl: 'static/frontend/views/folder-exists-modal.html',
            scope: $scope,
            controller: 'OverwriteModalInstanceCtrl',
            controllerAs: '$ctrl',
            resolve: {
                data: function () {
                    return {
                        file: folder,
                        type: fileToOverwrite.type
                    };
                }
            },
        })
        modalInstance.result.then(function (data) {
            listViewService.deleteWorkareaFile(vm.workarea, $scope.previousGridArraysString(), fileToOverwrite)
                .then(function () {
                    listViewService.addNewFolder($scope.ip, $scope.previousGridArraysString(), folder)
                        .then(function () {
                            $scope.updateGridArray();
                        });
                })
        });
    }
    $scope.newDirModal = function () {
        var modalInstance = $uibModal.open({
            animation: true,
            ariaLabelledBy: 'modal-title',
            ariaDescribedBy: 'modal-body',
            templateUrl: 'static/frontend/views/new-dir-modal.html',
            scope: $scope,
            controller: 'ModalInstanceCtrl',
            controllerAs: '$ctrl',
            resolve: {
                data: {}
            }
        })
        modalInstance.result.then(function (data) {
            $scope.createFolder(data.dir_name);
        });
    }
    $scope.removeFiles = function () {
        $scope.selectedCards.forEach(function (file) {
            listViewService.deleteWorkareaFile(vm.workarea, $scope.previousGridArraysString(), file)
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
    $scope.getFileExtension = function (file) {
        return file.name.split(".").pop().toUpperCase();
    }

    // **********************************
    //            Upload
    // **********************************

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
        return {destination: $scope.previousGridArraysString()};
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
            listViewService.deleteWorkareaFile(vm.workarea, $scope.previousGridArraysString(), file)
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
            flowObj.opts.query = {destination: $scope.previousGridArraysString()};
        });
        $rootScope.flowObjects[ip.id] = flowObj;
    }
});
