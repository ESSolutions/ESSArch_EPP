angular.module('myApp').controller('CreateDipCtrl', function($scope, $rootScope, $state, $stateParams, $controller, $cookies, $http, $interval, appConfig, $timeout, $anchorScroll, $uibModal, $translate) {
    $controller('BaseCtrl', { $scope: $scope });
    var vm = this;
    $scope.select = true;
    $scope.ip = $stateParams.ip;
    $http.get("static/frontend/scripts/json_data/orders.json").then(function(response) {
        $scope.orderObjects = response.data.orders;
    });
    if($scope.ip != null) {
        $scope.selectIp($scope.ip);
    }
    vm.itemsPerPage = $cookies.get('epp-ips-per-page') || 10;
    //context menu data
    $scope.menuOptions = function() {
        return [
        [$translate.instant('APPLYCHANGES'), function($itemScope, $event, modelValue, text, $li) {
            $scope.selectIp($itemScope.row);
        }],
        ];
    }
    //Cancel update intervals on state change
    $rootScope.$on('$stateChangeStart', function() {
        $interval.cancel(stateInterval);
        $interval.cancel(listViewInterval);
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
            $http.get('static/frontend/scripts/json_data/ips.json').then(function(response) {
                vm.displayedIps = response.data.create_dip;
                $scope.ipLoading = false;
            });
            /*Resource.getIpPage(start, number, pageNumber, tableState, $scope.selectedIp, sorting, search, ipSortString).then(function (result) {
                ctrl.displayedIps = result.data;
                tableState.pagination.numberOfPages = result.numberOfPages;//set the number of pages so the pagination can update
                $scope.ipLoading = false;
                $scope.initLoad = false;
            });*/
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
        if ($scope.select && $scope.ip.id == row.id) {
            $scope.select = false;
            $scope.eventlog = false;
            $scope.edit = false;
            $scope.requestForm = false;
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
        $scope.select = false;
        $scope.edit = false;
        $scope.eventlog = false;
        $scope.selectedCards1 = [];
        $scope.selectedCards2 = [];
        $scope.chosenFiles = [];
        $scope.deckGridData = [];
        $scope.selectIp(ip);
        $timeout(function() {
            $anchorScroll();
        });
    }
    //Deckgrid
    $scope.chosenFiles = [];
    $scope.chooseFiles = function(files) {
        files.forEach(function(file) {
            $scope.chosenFiles.push(angular.copy(file));
        });
        $scope.selectedCards1 = [];
    }
    $scope.removeFiles = function(files) {
        $scope.selectedCards2.forEach(function(file) {
            $scope.chosenFiles.splice($scope.chosenFiles.indexOf(file), 1);
        });
        $scope.selectedCards2 = [];        
    }
    $scope.previousGridArrays = [];
    $scope.previousGridArraysString = function() {
        var retString = "";
        $scope.previousGridArrays.forEach(function(card) {
            retString = retString.concat(card.name, "/");
        });
        return retString;
    }
    $scope.deckGridData = [];
    $scope.deckGridInit = function(ip) {
        $http.get("static/frontend/scripts/json_data/file_list.json").then(function(response) {
            $scope.deckGridData = response.data.ip_folder_list;
        });
    };
    $scope.previousGridArray = function() {
        $scope.previousGridArrays.pop();
        if($scope.previousGridArraysString() == "") {
            $scope.deckGridInit($scope.ip);
        } else {
            $http.get("static/frontend/scripts/json_data/file_list.json").then(function(response) {
                $scope.deckGridData = response.data.file_list;
            })
        }
    };
    $scope.updateGridArray = function(ip) {
        listViewService.getDir($scope.ip, $scope.previousGridArraysString()).then(function(dir) {
            $scope.deckGridData = dir;
        });
    };
    $scope.expandFile = function(whichArray, ip, card) {
        if (card.type == "dir") {
            var fileList;
            if($scope.previousGridArraysString() == "") {
                fileList = "file_list";
            } else {
                fileList = "sub_file_list";
            }
            $http.get("static/frontend/scripts/json_data/file_list.json").then(function(response) {
                if(whichArray == 1) {
                    $scope.deckGridData = response.data[fileList];
                    $scope.selectedCards1 = [];
                }
                $scope.previousGridArrays.push(card);
            });
        }
    };
    $scope.selectedCards1 = [];
    $scope.selectedCards2 = [];
    $scope.cardSelect = function(whichArray, card) {
        if(whichArray == 1) {
            if ($scope.selectedCards1.includes(card)) {
                $scope.selectedCards1.splice($scope.selectedCards1.indexOf(card),1);
            } else {
                $scope.selectedCards1.push(card);
            }
        } else {
            if ($scope.selectedCards2.includes(card)) {
                $scope.selectedCards2.splice($scope.selectedCards2.indexOf(card),1);
            } else {
                $scope.selectedCards2.push(card);
            }
        }
    };
    $scope.isSelected = function(whichArray, card) {
        var cardClass = "";
        if(whichArray == 1) {
            $scope.selectedCards1.forEach(function(file) {
                if(card == file) {
                    cardClass = "card-selected";
                }
            });
        } else {
            $scope.selectedCards2.forEach(function(file) {
                if(card == file) {
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
        modalInstance.closed.then(function (data) {
        });
    }
    $scope.searchDisabled = function () {
        if ($scope.filterModels.length > 0) {
            if ($scope.filterModels[0].column != null) {
                delete $scope.tableState.search.predicateObject;
                return true;
            }
        } else {
            return false;
        }
    }
    $scope.clearSearch = function () {
        delete $scope.tableState.search.predicateObject;
        $('#search-input')[0].value = "";
        $scope.getListViewData();
    }
});