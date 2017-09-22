angular.module('myApp').controller('AccessWorkareaCtrl', function (WorkareaFiles, Workarea, $scope, $controller, $rootScope, Resource, $interval, $timeout, appConfig, $cookies, $anchorScroll, $translate, $state, $http, listViewService, Requests, $uibModal, $sce, $window) {
    var vm = this;
    var ipSortString = "";
    vm.workarea = 'access';

    $controller('BaseCtrl', { $scope: $scope, vm: vm, ipSortString: ipSortString });

    vm.archived = null;

    $scope.menuOptions = function () {
        return [
        ];
    }

    // Remove ip
    $scope.removeIp = function (ipObject) {
        if(ipObject.package_type == 1) {
            ipObject.information_packages.forEach(function(ip) {
                $scope.removeIp(ip);
            });
        } else {
            Workarea.delete({
                id: ipObject.workarea.id
            }).$promise.then(function() {
                $scope.edit = false;
                $scope.select = false;
                $scope.eventlog = false;
                $scope.eventShow = false;
                $scope.statusShow = false;
                $scope.filebrowser = false;
                $scope.requestForm = false;
                if(vm.displayedIps.length == 0) {
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
            if(!$scope.select && !$scope.edit && !$scope.statusShow && !$scope.eventShow) {
                $scope.ip = null;
                $rootScope.ip = null;
            }
        } else {
            if ($rootScope.auth.id == ip.responsible.id || !ip.responsible) {
                $scope.filebrowser = true;
                $scope.ip = ip;
                $rootScope.ip = ip;
                $scope.deckGridInit($scope.ip);
                if(!$rootScope.flowObjects[$scope.ip.object_identifier_value]) {
                    $scope.createNewFlow($scope.ip);
                }
                $scope.currentFlowObject = $rootScope.flowObjects[$scope.ip.object_identifier_value];
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
    $scope.deckGridInit = function (ip) {
        listViewService.getWorkareaDir("access", $scope.previousGridArraysString()).then(function (dir) {
            $scope.deckGridData = dir;
        });
    };

    $scope.previousGridArray = function () {
        $scope.previousGridArrays.pop();
        listViewService.getWorkareaDir("access", $scope.previousGridArraysString()).then(function (dir) {
            $scope.deckGridData = dir;
            $scope.selectedCards = [];
        });
    };
    $scope.gridArrayLoading = false;
    $scope.updateGridArray = function (ip) {
        $scope.gridArrayLoading = true;
        listViewService.getWorkareaDir("access", $scope.previousGridArraysString()).then(function (dir) {
            $scope.deckGridData = dir;
            $scope.gridArrayLoading = false;
        });
    };
    $scope.expandFile = function (ip, card) {
        if (card.type == "dir" || card.name.endsWith('.tar') || card.name.endsWith('.zip')) {
            $scope.previousGridArrays.push(card);
            listViewService.getWorkareaDir("access", $scope.previousGridArraysString()).then(function (dir) {
                $scope.deckGridData = dir;
                $scope.selectedCards = [];
            }).catch(function(response) {
                $scope.previousGridArrays.pop();
                if(response.status == 200) {
                    $scope.getFile(card);
                }
            });
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
            listViewService.addNewWorkareaFolder("access", $scope.previousGridArraysString(), folder)
                .then(function (response) {
                    $scope.updateGridArray();
                });
        }
    }

    $scope.getFile = function (file) {
        file.content = $sce.trustAsResourceUrl(appConfig.djangoUrl + "workarea-files/?type=access&path=" + $scope.previousGridArraysString() + file.name);
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
            listViewService.deleteWorkareaFile("access", $scope.previousGridArraysString(), fileToOverwrite)
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
        })
        modalInstance.result.then(function (data) {
            $scope.createFolder(data.dir_name);
        });
    }
    $scope.removeFiles = function () {
        $scope.selectedCards.forEach(function (file) {
            listViewService.deleteWorkareaFile("access", $scope.previousGridArraysString(), file)
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
        console.log("set target");
        return appConfig.djangoUrl + 'workarea-files/upload/?type=access/';
    };
    $scope.getQuery = function(FlowFile, FlowChunk, isTest) {
        return {destination: $scope.previousGridArraysString()};
    };
    $scope.fileUploadSuccess = function(ip, file, message, flow) {
        $scope.uploadedFiles ++;
        var path = flow.opts.query.destination + file.relativePath;

        WorkareaFiles.mergeChunks({
            type: "ingest",
        }, { path: path });
    };
    $scope.fileTransferFilter = function(file)
    {
        return file.isUploading();
    };
    $scope.removeFiles = function() {
        $scope.selectedCards.forEach(function(file) {
            listViewService.deleteWorkareaFile("access", $scope.previousGridArraysString(), file)
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
            target: appConfig.djangoUrl+'workarea-files/upload/?type=access',
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
        $rootScope.flowObjects[ip.object_identifier_value] = flowObj;
    }
});
