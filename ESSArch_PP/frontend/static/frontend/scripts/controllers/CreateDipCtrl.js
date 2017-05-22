angular.module('myApp').controller('CreateDipCtrl', function($scope, $rootScope, $state, $stateParams, $controller, $cookies, $http, $interval, appConfig, $timeout, $anchorScroll, $uibModal, $translate, listViewService, Resource) {
    $controller('BaseCtrl', { $scope: $scope });
    var vm = this;
    $scope.select = true;
    $scope.ip = $stateParams.ip;
    $scope.orderObjects = [];
    listViewService.getOrderPage().then(function(response) {
        $scope.orderObjects = response.data;
    });
    if ($scope.ip != null) {
        $scope.selectIp($scope.ip);
    }
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
        return $http({
            method: 'GET',
            url: appConfig.djangoUrl + 'archive_policies/'
        }).then(function(response) {
            return response.data;
        });
    }
    $scope.archivePolicyChange = function() {
        vm.request.informationClass = vm.request.archivePolicy.value.information_class;
    }
    //context menu data
    $scope.menuOptions = function() {
        var label = $translate.instant('PRESERVE');
        if($scope.requestForm) {
            label = $translate.instant("CANCELPRESERVATION");
        }
        return [
            [label, function($itemScope, $event, modelValue, text, $li) {
                $scope.openRequestForm($itemScope.row);
            }],
        ];
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
			return;
		}
		if($scope.requestForm && $scope.ip.id== row.id){
			$scope.select = false;
			$scope.eventlog = false;
			$scope.edit = false;
			$scope.eventShow = false;
			$scope.requestForm = false;
            $scope.requestEventlog = false;
            $scope.selectIp(row);
		} else {
			$scope.select = false;
			$scope.eventlog = false;
			$scope.edit = false;
			$scope.eventShow = false;
			$scope.ip = row;
			$rootScope.ip = $scope.ip;
            $scope.getArchivePolicies().then(function(result) {
                vm.request.archivePolicy.options = result;
                $scope.requestForm = true;
                $scope.requestEventlog = true;
                row.class = "selected";
                $scope.selectedIp = row;
                $scope.eventsClick(row);
                $timeout(function() {
                    $anchorScroll("request-form");
                });
            });
		}
		$scope.statusShow = false;
    }

	$scope.submitRequest = function(ip, request) {
		switch(request.type) {
			case "preserve":
				$scope.preserveIp(ip, request);
				break;
			case "view":
				console.log("request not implemented");
				break;
			case "edit_as_new":
				console.log("request not implemented");
				break;
			case "diff_check":
				console.log("request not implemented");
				break;
			default:
				console.log("request not matched");
				break;
		}
	}
	$scope.preserveIp = function(ip, request) {
		listViewService.preserveIp(ip, {purpose: request.purpose, policy: request.archivePolicy.value.id}).then(function(result) {
			$scope.requestForm = false;
			$scope.eventlog = false;
			$scope.eventShow = false;
            $scope.requestEventlog = false;
			$scope.initRequestData();
			$scope.getListViewData();
		});
	}
    //Cancel update intervals on state change
    $rootScope.$on('$stateChangeStart', function() {
        $interval.cancel(stateInterval);
        $interval.cancel(listViewInterval);
        $interval.cancel(fileBrowserInterval);
    });
    // Click funtion columns that does not have a relevant click function
    $scope.ipRowClick = function(row) {
        $scope.selectIp(row);
        if ($scope.ip == row) {
            row.class = "";
            $scope.selectedIp = { id: "", class: "" };
        }
        if ($scope.eventShow) {
            $scope.eventsClick(row);
        }
        if ($scope.statusShow) {
            $scope.stateClicked(row);
        }
        if ($scope.select) {
            $scope.ipTableClick(row);
        }
    }
    //Click function for status view
    var stateInterval;
    $scope.stateClicked = function(row) {
        if ($scope.statusShow && $scope.ip == row) {
            $scope.statusShow = false;
        } else {
            $scope.statusShow = true;
            $scope.edit = false;
            $scope.statusViewUpdate(row);
        }
        $scope.subSelect = false;
        $scope.eventlog = false;
        $scope.select = false;
        $scope.eventShow = false;
        $scope.ip = row;
        $rootScope.ip = row;
    };
    //Click funciton for event view
	$scope.eventsClick = function (row) {
		if($scope.eventShow && $scope.ip == row){
			$scope.eventShow = false;
			$rootScope.stCtrl = null;
		} else {
			if($rootScope.stCtrl) {
				$rootScope.stCtrl.pipe();
			}
			$scope.eventShow = true;
			$scope.statusShow = false;
		}
		$scope.ip = row;
		$rootScope.ip = row;
	};
    //Initialize file browser update interval
    var fileBrowserInterval;
    $scope.$watch(function() { return $scope.select; }, function(newValue, oldValue) {
        if (newValue) {
            $interval.cancel(fileBrowserInterval);
            fileBrowserInterval = $interval(function() { $scope.updateGridArray() }, appConfig.fileBrowserInterval);
        } else {
            $interval.cancel(fileBrowserInterval);
        }
    });
    //If status view is visible, start update interval
    $scope.$watch(function() { return $scope.statusShow; }, function(newValue, oldValue) {
        if (newValue) {
            $interval.cancel(stateInterval);
            stateInterval = $interval(function() { $scope.statusViewUpdate($scope.ip) }, appConfig.stateInterval);
        } else {
            $interval.cancel(stateInterval);
        }
    });
    $scope.$watch(function() { return $rootScope.ipUrl; }, function(newValue, oldValue) {
        $scope.getListViewData();
    }, true);
    /*******************************************/
    /*Piping and Pagination for List-view table*/
    /*******************************************/

    var ctrl = this;
    $scope.selectedIp = { id: "", class: "" };
    $scope.selectedProfileRow = { profile_type: "", class: "" };
    this.displayedIps = [];
    //Get data according to ip table settings and populates ip table
    this.callServer = function callServer(tableState) {
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
            Resource.getDips(start, number, pageNumber, tableState, $scope.selectedIp, sorting, search, $scope.columnFilters).then(function (result) {
                ctrl.displayedIps = result.data;
                tableState.pagination.numberOfPages = result.numberOfPages;//set the number of pages so the pagination can update
                $scope.ipLoading = false;
                $scope.initLoad = false;
            });
        }
    };
    //Make ip selected and add class to visualize
    $scope.selectIp = function(row) {
        vm.displayedIps.forEach(function(ip) {
            if (ip.id == $scope.selectedIp.id) {
                ip.class = "";
            }
        });
        if (row.id == $scope.selectedIp.id) {
            $scope.selectedIp = { id: "", class: "" };
        } else {
            row.class = "selected";
            $scope.selectedIp = row;
        }
    };
    //Get data for list view
    $scope.getListViewData = function() {
        vm.callServer($scope.tableState);
        $rootScope.loadTags();
    };
    //Update ip list view with an interval
    //Update only if status < 100 and no step has failed in any IP
    var listViewInterval;

    function updateListViewConditional() {
        $interval.cancel(listViewInterval);
        listViewInterval = $interval(function() {
            var updateVar = false;
            vm.displayedIps.forEach(function(ip, idx) {
                if (ip.status < 100) {
                    if (ip.step_state != "FAILURE") {
                        updateVar = true;
                    }
                }
            });
            if (updateVar) {
                $scope.getListViewData();
            } else {
                $interval.cancel(listViewInterval);
                listViewInterval = $interval(function() {
                    var updateVar = false;
                    vm.displayedIps.forEach(function(ip, idx) {
                        if (ip.status < 100) {
                            if (ip.step_state != "FAILURE") {
                                updateVar = true;
                            }
                        }
                    });
                    if (!updateVar) {
                        $scope.getListViewData();
                    } else {
                        updateListViewConditional();
                    }

                }, appConfig.ipIdleInterval);
            }
        }, appConfig.ipInterval);
    };
    updateListViewConditional();

    //Click function for Ip table
    $scope.ipTableClick = function(row) {
        if ( row.State === "Creating" || row.State === "Created" || (($scope.select || $scope.requestForm) && $scope.ip.id == row.id)) {
            $scope.select = false;
            $scope.eventlog = false;
            $scope.edit = false;
        } else {
            $scope.ip = row;
            $rootScope.ip = $scope.ip;
            $scope.select = true;
            $scope.eventlog = true;
            $scope.edit = true;
            $scope.deckGridInit(row);
            $timeout(function() {
                $anchorScroll("select-view");
            }, 0);
        }
        $scope.requestForm = false;
        $scope.requestEventlog = false;
        $scope.eventShow = false;
        $scope.statusShow = false;
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
        $http({
            method: 'DELETE',
            url: ipObject.url
        }).then(function() {
            vm.displayedIps.splice(vm.displayedIps.indexOf(ipObject), 1);
            $scope.edit = false;
            $scope.select = false;
            $scope.eventlog = false;
            $scope.eventShow = false;
            $scope.statusShow = false;
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
            $scope.selectIp(ip);
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
    $scope.deckGridInit = function(ip) {
        listViewService.getWorkareaDir("access", null).then(function(workareaDir) {
            listViewService.getDipDir(ip, null).then(function(dipDir) {
                $scope.deckGridData = workareaDir;
                $scope.chosenFiles = dipDir;
                $scope.previousGridArrays1 = [];
                $scope.previousGridArrays2 = [];
            });
        });
    };
    $scope.previousGridArray = function(whichArray) {
        if (whichArray == 1) {
            $scope.previousGridArrays1.pop();
            if ($scope.previousGridArraysString(1) == "") {
                listViewService.getWorkareaDir("access", null).then(function(workareaDir) {
                    $scope.deckGridData = workareaDir;
                });
            } else {
                listViewService.getWorkareaDir("access", $scope.previousGridArraysString(1)).then(function(dir) {
                    $scope.deckGridData = dir;
                })
            }
        } else {
            $scope.previousGridArrays2.pop();
            if ($scope.previousGridArraysString(2) == "") {
                listViewService.getDipDir($scope.ip, null).then(function(dipDir) {
                    $scope.chosenFiles = dipDir;
                });
            } else {
                listViewService.getDipDir($scope.ip, $scope.previousGridArraysString(2)).then(function(dir) {
                    $scope.chosenFiles = dir;
                })
            }
        }
    };
    $scope.workArrayLoading = false;
    $scope.dipArrayLoading = false;
    $scope.updateGridArray = function() {
        $scope.updateWorkareaFiles();
        $scope.updateDipFiles();
    };
    $scope.updateWorkareaFiles = function () {
        $scope.workArrayLoading = true;
        return listViewService.getWorkareaDir("access", $scope.previousGridArraysString(1)).then(function (dir) {
            $scope.deckGridData = dir;
            $scope.workArrayLoading = false;
        });

    }
    $scope.updateDipFiles = function () {
        $scope.dipArrayLoading = true;
        return listViewService.getDipDir($scope.ip, $scope.previousGridArraysString(2)).then(function (dirir) {
            $scope.chosenFiles = dirir;
            $scope.dipArrayLoading = false;
        });
    }
    $scope.expandFile = function(whichArray, ip, card) {
        if (card.type == "dir") {
            if (whichArray == 1) {
                listViewService.getWorkareaDir("access", $scope.previousGridArraysString(1) + card.name).then(function (dir) {
                    $scope.deckGridData = dir;
                    $scope.selectedCards1 = [];
                    $scope.previousGridArrays1.push(card);
                });
            } else {
                listViewService.getDipDir(ip, $scope.previousGridArraysString(2) + card.name).then(function (dir) {
                    $scope.chosenFiles = dir;
                    $scope.selectedCards2 = [];
                    $scope.previousGridArrays2.push(card);
                });
            }
        }
    };
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

    $scope.prepareDipModal = function() {
        var modalInstance = $uibModal.open({
            animation: true,
            ariaLabelledBy: 'modal-title',
            ariaDescribedBy: 'modal-body',
            templateUrl: 'static/frontend/views/prepare-dip-modal.html',
            scope: $scope,
            controller: 'ModalInstanceCtrl',
            controllerAs: '$ctrl'
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
            controllerAs: '$ctrl'
        })
        modalInstance.result.then(function(data) {
            $scope.createDipFolder(data.dir_name);
        });
    }
    $scope.searchDisabled = function() {
        if ($scope.filterModels.length > 0) {
            if ($scope.filterModels[0].column != null) {
                delete $scope.tableState.search.predicateObject;
                return true;
            }
        } else {
            return false;
        }
    }
    $scope.clearSearch = function() {
        delete $scope.tableState.search.predicateObject;
        $('#search-input')[0].value = "";
        $scope.getListViewData();
    }
});