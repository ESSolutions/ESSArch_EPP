angular.module('myApp').controller('CreateDipCtrl', function(IP, ArchivePolicy, $scope, $rootScope, $state, $stateParams, $controller, $cookies, $http, $interval, appConfig, $timeout, $anchorScroll, $uibModal, $translate, listViewService, Resource, Requests, $sce, $window) {
    var vm = this;
    var ipSortString = "";
    var watchers = [];
    $controller('BaseCtrl', { $scope: $scope, vm: vm, ipSortString: ipSortString });
    $scope.orderObjects = [];
    listViewService.getOrderPage().then(function(response) {
        $scope.orderObjects = response.data;
    });
    vm.itemsPerPage = $cookies.get('epp-ips-per-page') || 10;
    $scope.initRequestData = function () {
		vm.request = {
			type: "preserve",
			purpose: "",
            archivePolicy: {
                value: null,
                options: []
            },
		};
	}
    $scope.initRequestData();

    $scope.getArchivePolicies = function() {
        return ArchivePolicy.query().$promise.then(function(data) {
            return data;
        });
    }
    $scope.archivePolicyChange = function() {
        vm.request.informationClass = vm.request.archivePolicy.value.information_class;
    }
    //context menu data
    $scope.menuOptions = function() {
        return [];
    }
    $scope.requestForm = false;
    $scope.openRequestForm = function(row) {
        if(row.package_type == 1) {
			$scope.select = false;
			$scope.eventlog = false;
			$scope.edit = false;
			$scope.eventShow = false;
			$scope.requestForm = false;
            $scope.requestEventlog = false;
            if ($scope.ip != null && $scope.ip.object_identifier_value== row.object_identifier_value) {
				$scope.ip = null;
				$rootScope.ip = null;
			} else {
				$scope.ip = row;
				$rootScope.ip = $scope.ip;
			}
			return;
		}
		if($scope.requestForm && $scope.ip.id== row.id){
			$scope.select = false;
			$scope.eventlog = false;
			$scope.edit = false;
			$scope.eventShow = false;
			$scope.requestForm = false;
            $scope.requestEventlog = false;
            $scope.ip = null;
			$rootScope.ip = null;
		} else {
			$scope.select = false;
			$scope.eventlog = false;
			$scope.edit = false;
            $scope.eventShow = false;
            $scope.requestForm = true;
            $scope.requestEventlog = true;
            $scope.eventShow = false;
			$scope.ip = row;
            $rootScope.ip = $scope.ip;
            $scope.getArchivePolicies().then(function(data) {
                vm.request.archivePolicy.options = data;
            })
		}
		$scope.statusShow = false;
    }

    //Cancel update intervals on state change
    $rootScope.$on('$stateChangeStart', function() {
        $interval.cancel(fileBrowserInterval);
        watchers.forEach(function(watcher) {
            watcher();
        });
    });


    //Initialize file browser update interval
    var fileBrowserInterval;
    watchers.push($scope.$watch(function() { return $scope.select; }, function(newValue, oldValue) {
        if (newValue) {
            $interval.cancel(fileBrowserInterval);
            fileBrowserInterval = $interval(function() { $scope.updateGridArray() }, appConfig.fileBrowserInterval);
        } else {
            $interval.cancel(fileBrowserInterval);
        }
    }));
    /*******************************************/
    /*Piping and Pagination for List-view table*/
    /*******************************************/

    vm.displayedIps = [];
    //Get data according to ip table settings and populates ip table
    vm.callServer = function callServer(tableState) {
        $scope.ipLoading = true;
        if (vm.displayedIps.length == 0) {
            $scope.initLoad = true;
        }
        if (!angular.isUndefined(tableState)) {
            $scope.tableState = tableState;
            var search = "";
            if (tableState.search.predicateObject) {
                var search = tableState.search.predicateObject["$"];
            }
            var sorting = tableState.sort;
            var pagination = tableState.pagination;
            var start = pagination.start || 0; // This is NOT the page number, but the index of item in the list that you want to use to display the table.
            var number = pagination.number || vm.itemsPerPage; // Number of entries showed per page.
            var pageNumber = start / number + 1;
            Resource.getDips(start, number, pageNumber, tableState, sorting, search, $scope.columnFilters).then(function (result) {
                vm.displayedIps = result.data;
                tableState.pagination.numberOfPages = result.numberOfPages;//set the number of pages so the pagination can update
                $scope.ipLoading = false;
                $scope.initLoad = false;
            });
        }
    };


    //Click function for Ip table
    $scope.ipTableClick = function (row) {
        if (row.state == "Created") {
            $scope.openRequestForm(row);
        } else {

            if (row.state === "Creating" || (($scope.select || $scope.requestForm) && $scope.ip.id == row.id)) {
                $scope.select = false;
                $scope.eventlog = false;
                $scope.edit = false;
                $scope.ip = null;
                $rootScope.ip = null;
                $scope.filebrowser = false;
            } else {
                $scope.ip = row;
                $rootScope.ip = $scope.ip;
                $scope.select = true;
                $scope.eventlog = true;
                $scope.edit = true;
                $scope.filesPerPage = $cookies.get("files-per-page") || 50;
                $scope.dipFilesPerPage = $cookies.get("files-per-page") || 50;
                $scope.deckGridInit(row);
            }
            $scope.requestForm = false;
            $scope.requestEventlog = false;
            $scope.eventShow = false;
            $scope.statusShow = false;
        }
    };
        $scope.colspan = 9;
        $scope.stepTaskInfoShow = false;
        $scope.statusShow = false;
        $scope.eventShow = false;
        $scope.select = false;
        $scope.subSelect = false;
        $scope.edit = false;
        $scope.eventlog = false;
        $scope.requestForm = false;

    $scope.removeIp = function(ipObject) {
        IP.delete({
            id: ipObject.id
        }).$promise.then(function() {
            vm.displayedIps.splice(vm.displayedIps.indexOf(ipObject), 1);
            $scope.edit = false;
            $scope.select = false;
            $scope.eventlog = false;
            $scope.eventShow = false;
            $scope.statusShow = false;
            if(vm.displayedIps.length == 0) {
                $state.reload();
            }
            $scope.getListViewData();
        });
    }

    $scope.createDip = function(ip) {
        listViewService.createDip(ip).then(function(response) {
            $scope.select = false;
            $scope.edit = false;
            $scope.eventlog = false;
            $scope.selectedCards1 = [];
            $scope.selectedCards2 = [];
            $scope.chosenFiles = [];
            $scope.deckGridData = [];
            $timeout(function() {
                $scope.getListViewData();
                $anchorScroll();
            });
        })
        }
        //Deckgrid
    $scope.chosenFiles = [];
    $scope.chooseFiles = function(files) {
        var fileExists = false;
        files.forEach(function(file) {
            $scope.chosenFiles.forEach(function(chosen, index) {
                if (chosen.name === file.name) {
                    fileExists = true;
                    fileExistsModal(index, file, chosen);
                }
            });
            if (!fileExists) {
                listViewService.addFileToDip($scope.ip, $scope.previousGridArraysString(1), file, $scope.previousGridArraysString(2), "access")
                    .then(function (result) {
                        $scope.updateGridArray();
                    });
            }
        });
        $scope.selectedCards1 = [];
    }
    function fileExistsModal(index, file, fileToBeOverwritten) {
        var modalInstance = $uibModal.open({
            animation: true,
            ariaLabelledBy: 'modal-title',
            ariaDescribedBy: 'modal-body',
            templateUrl: 'static/frontend/views/file-exists-modal.html',
            scope: $scope,
            resolve: {
                data: function() {
                    return {
                        file: file,
                        type: fileToBeOverwritten.type
                    };
                }
            },
            controller: 'OverwriteModalInstanceCtrl',
            controllerAs: '$ctrl'
        })
        modalInstance.result.then(function (data) {
            listViewService.addFileToDip($scope.ip, $scope.previousGridArraysString(1), file, $scope.previousGridArraysString(2), "access")
                .then(function (result) {
                    $scope.updateGridArray();
                });
        });
    }

    function folderNameExistsModal(index, folder, fileToBeOverwritten) {
        var modalInstance = $uibModal.open({
            animation: true,
            ariaLabelledBy: 'modal-title',
            ariaDescribedBy: 'modal-body',
            templateUrl: 'static/frontend/views/file-exists-modal.html',
            scope: $scope,
            controller: 'OverwriteModalInstanceCtrl',
            controllerAs: '$ctrl',
            resolve: {
                data: function() {
                    return {
                        file: folder,
                        type: fileToBeOverwritten.type
                    };
                }
            },
        })
        modalInstance.result.then(function(data) {
            listViewService.deleteFile($scope.ip, $scope.previousGridArraysString(2), fileToBeOverwritten)
                .then(function(){
                    listViewService.addNewFolder($scope.ip, $scope.previousGridArraysString(2), folder)
                        .then(function() {
                            $scope.updateGridArray();
                        });
                });
        });
    }

    $scope.removeFiles = function() {
        $scope.selectedCards2.forEach(function(file) {
            listViewService.deleteFile($scope.ip, $scope.previousGridArraysString(2), file)
            .then(function () {
                $scope.updateGridArray();
            });
        });
        $scope.selectedCards2 = [];
    }

    $scope.createDipFolder = function(folderName) {
        var folder = {
            "type": "dir",
            "name": folderName
        };
        var fileExists = false;
        $scope.chosenFiles.forEach(function(chosen, index) {
            if (chosen.name === folder.name) {
                fileExists = true;
                folderNameExistsModal(index, folder, chosen);
            }
        });
        if (!fileExists) {
            listViewService.addNewFolder($scope.ip, $scope.previousGridArraysString(2), folder)
                .then(function (response) {
                    $scope.updateGridArray();
                });
        }
    }
    $scope.previousGridArrays1 = [];
    $scope.previousGridArrays2 = [];
    $scope.workareaListView = false;
    $scope.workareaGridView = true;
    $scope.dipListView = false;
    $scope.dipGridView = true;
    $scope.useListView = function(whichArray) {
        if(whichArray === 1) {
            $scope.workareaListView = true;
            $scope.workareaGridView = false;
            $scope.filesPerPage = $cookies.get("files-per-page") || 50;

        } else {
            $scope.dipListView = true;
            $scope.dipGridView = false;
            $scope.dipFilesPerPage = $cookies.get("files-per-page") || 50;

        }
    }

    $scope.useGridView = function(whichArray) {
        if(whichArray === 1) {
            $scope.workareaListView = false;
            $scope.workareaGridView = true;
            $scope.filesPerPage = $cookies.get("files-per-page") || 50;

        } else {
            $scope.dipListView = false;
            $scope.dipGridView = true;
            $scope.dipFilesPerPage = $cookies.get("files-per-page") || 50;

        }
    }

    $scope.changeFilesPerPage = function(filesPerPage) {
        $cookies.put("files-per-page", filesPerPage, { expires: new Date("Fri, 31 Dec 9999 23:59:59 GMT") });
    }
    $scope.previousGridArraysString = function(whichArray) {
        var retString = "";
        if (whichArray === 1) {
            $scope.previousGridArrays1.forEach(function(card) {
                retString = retString.concat(card.name, "/");
            });
        } else {
            $scope.previousGridArrays2.forEach(function(card) {
                retString = retString.concat(card.name, "/");
            });
        }
        return retString;
    }
    $scope.deckGridData = [];
    $scope.workareaPipe = function(tableState) {
        $scope.workArrayLoading = true;
        if ($scope.deckGridData.length == 0) {
            $scope.initLoad = true;
        }
        if (!angular.isUndefined(tableState)) {
            $scope.workarea_tableState = tableState;
            var pagination = $scope.workarea_tableState.pagination;
            var start = pagination.start || 0;     // This is NOT the page number, but the index of item in the list that you want to use to display the table.
            var number = pagination.number;  // Number of entries showed per page.
            var pageNumber = start / number + 1;
            listViewService.getWorkareaDir("access", $scope.previousGridArraysString(1), pageNumber, number).then(function(dir) {
                $scope.deckGridData = dir.data;
                $scope.workarea_tableState.pagination.numberOfPages = dir.numberOfPages;//set the number of pages so the pagination can update
                $scope.workArrayLoading = false;
                $scope.initLoad = false;
            })
        }
    }
    $scope.dipPipe = function(tableState) {
        $scope.gridArrayLoading = true;
        if ($scope.deckGridData.length == 0) {
            $scope.initLoad = true;
        }
        if (!angular.isUndefined(tableState)) {
            $scope.dip_tableState = tableState;
            var pagination = $scope.dip_tableState.pagination;
            var start = pagination.start || 0;     // This is NOT the page number, but the index of item in the list that you want to use to display the table.
            var number = pagination.number;  // Number of entries showed per page.
            var pageNumber = start / number + 1;
            listViewService.getDipDir($scope.ip, $scope.previousGridArraysString(2), pageNumber, number).then(function(dir) {
                $scope.chosenFiles = dir.data;
                $scope.dip_tableState.pagination.numberOfPages = dir.numberOfPages;//set the number of pages so the pagination can update
                $scope.gridArrayLoading = false;
                $scope.initLoad = false;
            })
        }
    }
    $scope.deckGridInit = function(ip) {
        $scope.previousGridArrays1 = [];
        $scope.previousGridArrays2 = [];
        if($scope.dip_tablestate && $sope.workarea_tablestate) {
            $scope.workareaPipe($scope.workarea_tableState);
            $scope.dipPipe($scope.dip_tableState);
        }
    };

    $scope.previousGridArray = function(whichArray) {
        if (whichArray == 1) {
            $scope.previousGridArrays1.pop();
            $scope.workareaPipe($scope.workarea_tableState);
        } else {
            $scope.previousGridArrays2.pop();
            $scope.dipPipe($scope.dip_tableState);
        }
    };
    $scope.workArrayLoading = false;
    $scope.dipArrayLoading = false;
    $scope.updateGridArray = function() {
        $scope.updateWorkareaFiles();
        $scope.updateDipFiles();
    };
    $scope.updateWorkareaFiles = function () {
        if($scope.workarea_tableState) {
            $scope.workareaPipe($scope.workarea_tableState);
        }
    }
    $scope.updateDipFiles = function () {
        if($scope.dip_tableState) {
            $scope.dipPipe($scope.dip_tableState);
        }
    }
    $scope.expandFile = function(whichArray, ip, card) {
        if (card.type == "dir") {
            if (whichArray == 1) {
                $scope.selectedCards1 = [];
                $scope.previousGridArrays1.push(card);
                if($scope.workarea_tableState) {
                    $scope.workarea_tableState.pagination.start = 0;
                    $scope.workareaPipe($scope.workarea_tableState);
                    $scope.selectedCards = [];
                }
            } else {
                $scope.selectedCards2 = [];
                $scope.previousGridArrays2.push(card);
                if($scope.dip_tableState) {
                    $scope.dip_tableState.pagination.start = 0;
                    $scope.dipPipe($scope.dip_tableState);
                    $scope.selectedCards = [];
                }
            }
        } else {
            $scope.getFile(card);
        }
    };
    $scope.getFile = function (file) {
        file.content = $sce.trustAsResourceUrl($scope.ip.url + "files/?path=" + $scope.previousGridArraysString() + file.name);
        $window.open(file.content, '_blank');
    }
    $scope.selectedCards1 = [];
    $scope.selectedCards2 = [];
    $scope.cardSelect = function(whichArray, card) {
        if (whichArray == 1) {
            if (includesWithProperty($scope.selectedCards1, "name", card.name)) {
                $scope.selectedCards1.splice($scope.selectedCards1.indexOf(card), 1);
            } else {
                $scope.selectedCards1.push(card);
            }
        } else {
            if (includesWithProperty($scope.selectedCards2, "name", card.name)) {
                $scope.selectedCards2.splice($scope.selectedCards2.indexOf(card), 1);
            } else {
                $scope.selectedCards2.push(card);
            }
        }
    };

    function includesWithProperty(array, property, value) {
        for(i=0; i < array.length; i++) {
            if(array[i][property] === value) {
                return true;
            }
        }
        return false;
    }

    $scope.isSelected = function(whichArray, card) {
        var cardClass = "";
        if (whichArray == 1) {
            $scope.selectedCards1.forEach(function(file) {
                if (card.name == file.name) {
                    cardClass = "card-selected";
                }
            });
        } else {
            $scope.selectedCards2.forEach(function(file) {
                if (card.name == file.name) {
                    cardClass = "card-selected";
                }
            });
        }
        return cardClass;
    };

    $scope.getFileExtension = function(file) {
        return file.name.split(".").pop().toUpperCase();
    }
    $scope.prepareDipModal = function() {
        var modalInstance = $uibModal.open({
            animation: true,
            ariaLabelledBy: 'modal-title',
            ariaDescribedBy: 'modal-body',
            templateUrl: 'static/frontend/views/prepare-dip-modal.html',
            scope: $scope,
            controller: 'ModalInstanceCtrl',
            controllerAs: '$ctrl',
            resolve: {
                data: {}
            }
        })
        modalInstance.result.then(function(data) {
            $scope.prepareDip(data.label, data.objectIdentifierValue, data.orders);
        });
    }

    $scope.prepareDip = function(label, objectIdentifierValue, orders) {
        listViewService.prepareDip(label, objectIdentifierValue, orders).then(function(response) {
            $timeout(function() {
                $scope.getListViewData();
            });
        });
    }

    $scope.newDirModal = function() {
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
        modalInstance.result.then(function(data) {
            $scope.createDipFolder(data.dir_name);
        });
    }
});
