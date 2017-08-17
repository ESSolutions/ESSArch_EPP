angular.module('myApp').controller('IngestWorkareaCtrl', function($scope, $controller, $rootScope, Resource, $interval, $timeout, appConfig, $cookies, $anchorScroll, $translate, $http, listViewService, Requests, $uibModal, $sce, $window) {
    var vm = this;
    var ipSortString = "";
    vm.workarea = 'ingest';

    $controller('BaseCtrl', { $scope: $scope, vm: vm, ipSortString: ipSortString });
    //context menu data
    $scope.menuOptions = function() {
        return [];
    }

    //Click function for Ip table
    $scope.ipTableClick = function(row) {
        if(row.package_type == 1) {
			$scope.select = false;
			$scope.eventlog = false;
			$scope.edit = false;
			$scope.eventShow = false;
            $scope.requestForm = false;
            if ($scope.ip != null && $scope.ip.object_identifier_value == row.object_identifier_value) {
                $scope.ip = null;
                $rootScope.ip = null;
                $scope.filebrowser = false;
            } else {
                $scope.ip = row;
                $rootScope.ip = $scope.ip;
            }
			$scope.initRequestData();
			return;
		}
        if($scope.select && $scope.ip.id == row.id){
            $scope.select = false;
            $scope.eventlog = false;
            $scope.edit = false;
            $scope.eventShow = false;
            $scope.requestForm = false;
            $scope.ip = false;
			$rootScope.ip = false
            $scope.filebrowser = false;
			$scope.initRequestData();
        } else {
            $scope.ip = row;
            $rootScope.ip = $scope.ip;
            $scope.select = true;
            $scope.eventlog = true;
            $scope.edit = true;
            $scope.requestForm = true;
            if (!$scope.eventsShow || $scope.ip.object_identifier_value != row.object_identifier_value) {
                $scope.eventShow = false;
                $scope.eventsClick(row);
            }
            $scope.ip = row;
			$rootScope.ip = $scope.ip;
        }
        $scope.statusShow = false;
    };
    
    // ***********************
    //       FILEBROWSER
    // ***********************

    $scope.previousGridArrays = [];
    $scope.ip = $rootScope.ip;
    $scope.previousGridArraysString = function () {
        var retString = $scope.ip.object_identifier_value + "/";
        $scope.previousGridArrays.forEach(function (card) {
            retString = retString.concat(card.name, "/");
        });
        return retString;
    }
    $scope.deckGridData = [];
    $scope.deckGridInit = function (ip) {
        listViewService.getWorkareaDir("ingest", $scope.previousGridArraysString()).then(function (dir) {
            $scope.deckGridData = dir;
        });
    };
    if ($scope.ip) {
        $scope.deckGridInit($scope.ip);
    }
    $scope.$watch(function () { return $scope.ip; }, function (newValue, oldValue) {
        if($scope.ip) {
            $scope.deckGridInit($scope.ip);
        }
        $scope.previousGridArrays = [];
    }, true);
    $scope.previousGridArray = function () {
        $scope.previousGridArrays.pop();
        listViewService.getWorkareaDir("ingest", $scope.previousGridArraysString()).then(function (dir) {
            $scope.deckGridData = dir;
            $scope.selectedCards = [];
        });
    };
    $scope.gridArrayLoading = false;
    $scope.updateGridArray = function (ip) {
        $scope.gridArrayLoading = true;
        listViewService.getWorkareaDir("ingest", $scope.previousGridArraysString()).then(function (dir) {
            $scope.deckGridData = dir;
            $scope.gridArrayLoading = false;
        });
    };
    $scope.expandFile = function (ip, card) {
        if (card.type == "dir" || card.name.endsWith('.tar') || card.name.endsWith('.zip')) {
            $scope.previousGridArrays.push(card);
            listViewService.getWorkareaDir("ingest", $scope.previousGridArraysString()).then(function (dir) {
                $scope.deckGridData = dir;
                $scope.selectedCards = [];
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
            listViewService.addNewWorkareaFolder("ingest", $scope.previousGridArraysString(), folder)
                .then(function (response) {
                    $scope.updateGridArray();
                });
        }
    }

    $scope.getFile = function (file) {
        file.content = $sce.trustAsResourceUrl(appConfig.djangoUrl + "workarea-files/?type=ingest&path=" + $scope.previousGridArraysString() + file.name);
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
            listViewService.deleteWorkareaFile("ingest", $scope.previousGridArraysString(), fileToOverwrite)
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
            listViewService.deleteWorkareaFile("ingest", $scope.previousGridArraysString(), file)
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
});
