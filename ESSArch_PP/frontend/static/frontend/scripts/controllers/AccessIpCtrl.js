angular.module('myApp').controller('AccessIpCtrl', function($scope, $controller, $rootScope, Resource, $interval, $timeout, appConfig, $cookies, $anchorScroll, $translate, $http, $state, Requests, $uibModal, $log) {
    var vm = this;
    var ipSortString = "";
    $controller('BaseCtrl', { $scope: $scope, vm: vm, ipSortString: ipSortString });
    vm.archived = true;

    $scope.ips = [];

    $scope.menuOptions = function(rowType) {
        return [
            {
                text: $translate.instant("APPRAISAL"),
                click: function ($itemScope, $event, modelValue, text, $li) {
                    if($scope.ips.length == 0 && $scope.ip == null) {
                    } else {
                        vm.openAppraisalModal($scope.ips);
                    }
                }
            },
            {
                text: $translate.instant("CONVERSION"),
                click: function ($itemScope, $event, modelValue, text, $li) {
                    if($scope.ips.length == 0 && $scope.ip == null) {
                    } else {
                        vm.openConversionModal($scope.ips);
                    }
                }
            },
        ];
    };

    var watchers = [];
    watchers.push($scope.$watch(function() {return $scope.ip}, function(newVal, oldVal) {
        if(newVal != null) {
            $scope.ips = [];
        }
    }))

    //Destroy watcers on state change
    $scope.$on('$stateChangeStart', function() {
        watchers.forEach(function(watcher) {
            watcher();
        });
    });
    //Click function for Ip table
    $scope.ipTableClick = function(row, event) {
        if( event && event.shiftKey) {
            shiftClickrow(row)
        } else if(event && event.ctrlKey) {
            altClickRow(row);
        } else {
            selectSingleRow(row);
        }
    };

    function shiftClickrow(row) {
        var index = vm.displayedIps.map(function(ip) { return ip.id; }).indexOf(row.id);
        var last;
        if($scope.ips.length > 0) {
            last = $scope.ips[$scope.ips.length-1].id;
        } else if ($scope.ips.length <= 0 && $scope.ip != null) {
            last = $scope.ip.id;
        } else {
            last = null;
        }
        var lastIndex = last != null?vm.displayedIps.map(function(ip) { return ip.id; }).indexOf(last):index;
        if(lastIndex > index) {
            for(i = lastIndex;i >= index;i--) {
                if(!$scope.selectedAmongOthers(vm.displayedIps[i].id)) {
                    $scope.ips.push(vm.displayedIps[i]);
                }
            }
        } else if(lastIndex < index) {
            for(i = lastIndex;i <= index;i++) {
                if(!$scope.selectedAmongOthers(vm.displayedIps[i].id)) {
                    $scope.ips.push(vm.displayedIps[i]);
                }
            }
        } else {
            selectSingleRow(row);
        }
        $scope.statusShow = false;
    }

    function altClickRow(row) {
        if(row.package_type != 1) {
            if($scope.ip != null) {
                $scope.ips.push($scope.ip);
            }
            $scope.ip = null;
            $rootScope.ip = null;
            $scope.eventShow = false;
            $scope.statusShow = false;
            $scope.filebrowser = false;
            var deleted = false;
            $scope.ips.forEach(function(ip, idx, array) {
                if(!deleted && ip.object_identifier_value == row.object_identifier_value) {
                    array.splice(idx, 1);
                    deleted = true;
                }
            })
            if(!deleted) {
                if($scope.ips.length ==  0) {
                    $scope.initRequestData();
                }
                $scope.select = true;
                $scope.eventlog = true;
                $scope.edit = true;
                $scope.requestForm = true;
                $scope.eventShow = false;
                $scope.ips.push(row);
            }
            if($scope.ips.length == 1) {
                $scope.ip = $scope.ips[0];
                $rootScope.ip = $scope.ips[0];
                $scope.ips = [];
            }
        }
        $scope.statusShow = false;
    }

    function selectSingleRow(row) {
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
            return;
        }
        $scope.ips = [];
        if($scope.select &&$scope.ip != null && $scope.ip.object_identifier_value == row.object_identifier_value){
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
    }

    $scope.selectedAmongOthers = function(id) {
        var exists = false;
        $scope.ips.forEach(function(ip, idx, array) {
            if(ip.id == id) {
                exists = true;
            }
        })
        return exists;
    }

    $scope.clickSubmit = function() {
        $scope.submitRequest($scope.ips, vm.request);
    }

    // Requests
    $scope.submitRequest = function(ips, request) {
        switch (request.type) {
            case "get":
            case "get_tar":
            case "get_as_new":
                if ($scope.ips.length) {
                    ips.forEach(function (ip) {
                        $scope.accessIp(ip, request);
                    })
                } else if($scope.ip != null) {
                    $scope.accessIp($scope.ip, request);
                }
                break;
            default:
                console.log("request not matched");
                break;
        }
    }

    vm.openAppraisalModal = function (ips) {
        if(ips.length == 0 && $scope.ip != null) {
            ips.push($scope.ip);
        }
        var modalInstance = $uibModal.open({
            animation: true,
            ariaLabelledBy: 'modal-title',
            ariaDescribedBy: 'modal-body',
            templateUrl: 'static/frontend/views/appraisal_modal.html',
            controller: 'AppraisalModalInstanceCtrl',
            controllerAs: '$ctrl',
            size: "lg",
            resolve: {
                data: function () {
                    return {
                        ips: ips,
                    };
                }
            },
        })
        modalInstance.result.then(function (data) {
        }, function () {
            $log.info('modal-component dismissed at: ' + new Date());
        });
    }

    vm.openConversionModal = function (ips) {
        if(ips.length == 0 && $scope.ip != null) {
            ips.push($scope.ip);
        }
        var modalInstance = $uibModal.open({
            animation: true,
            ariaLabelledBy: 'modal-title',
            ariaDescribedBy: 'modal-body',
            templateUrl: 'static/frontend/views/conversion_modal.html',
            controller: 'ConversionModalInstanceCtrl',
            controllerAs: '$ctrl',
            size: "lg",
            resolve: {
                data: function () {
                    return {
                        ips: ips,
                    };
                }
            },
        })
        modalInstance.result.then(function (data) {
        }, function () {
            $log.info('modal-component dismissed at: ' + new Date());
        });
    }

});
