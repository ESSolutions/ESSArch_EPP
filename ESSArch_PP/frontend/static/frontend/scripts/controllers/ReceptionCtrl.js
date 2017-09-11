/*
ESSArch is an open source archiving and digital preservation system

ESSArch Preservation Platform (EPP)
Copyright (C) 2005-2017 ES Solutions AB

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.

Contact information:
Web - http://www.essolutions.se
Email - essarch@essolutions.se
*/

angular.module('myApp').controller('ReceptionCtrl', function (IPReception, IP, Tag, ArchivePolicy, $log, $uibModal, $timeout, $scope, $window, $location, $sce, $http, myService, appConfig, $state, $stateParams, $rootScope, listViewService, $interval, Resource, $translate, $cookies, $cookieStore, $filter, $anchorScroll, PermPermissionStore, $q, $controller, Requests){
    var vm = this;
    var ipSortString = "";
    $controller('BaseCtrl', { $scope: $scope, vm: vm, ipSortString: ipSortString });
    $scope.includedIps = [];
    $scope.profileEditor = false;
    //Request form data
    $scope.initRequestData = function() {
        vm.request = {
            type: "receive",
            purpose: "",
            archivePolicy: {
                value: null,
                options: []
            },
            submissionAgreement: {
                value: null,
                options: [],
                disabled: false
            },
            tags: {
                value: [],
                options: []
            },
            informationClass: null,
            allowUnknownFiles: false
        };
    }
    $scope.initRequestData();
    $rootScope.$on('$stateChangeStart', function() {
        $interval.cancel(tagsInterval);
    });
    $scope.includeIp = function(row) {
        var temp = true;
        $scope.includedIps.forEach(function(included, index, array) {

            if(included.id == row.id) {
                $scope.includedIps.splice(index, 1);
                temp = false;
            }
        });
        if(temp) {
            $scope.includedIps.push({ id: row.id, at_reception: row.state == "At reception" });
        }
        if($scope.includedIps.length == 0) {
            $scope.initRequestData();
            $scope.requestForm = false;
        } else {
            if(!$scope.requestForm) {
                $scope.requestForm = true;
            }
        }
    }

    $scope.updateTags = function() {
        $scope.tagsLoading = true;
        $scope.getTags().then(function(result) {
            vm.request.tags.options = result;
            $scope.requestForm = true;
            $scope.tagsLoading = false;
        });
    }

    $scope.archivePolicyChange = function() {
        vm.request.informationClass = vm.request.archivePolicy.value.information_class;
    }

    //If status view is visible, start update interval
    var tagsInterval;
    $scope.$watch(function(){return $scope.requestForm}, function(newValue, oldValue) {
        if(newValue) {
            $interval.cancel(tagsInterval);
            tagsInterval = $interval(function(){$scope.updateTags()}, appConfig.tagsInterval);
        } else {
            $interval.cancel(tagsInterval);
        }
    });
    //Get data for status view

    /*******************************************/
    /*Piping and Pagination for List-view table*/
    /*******************************************/

    $scope.selectedProfileRow = {profile_type: "", class: ""};
    vm.displayedIps = [];
    //Get data according to ip table settings and populates ip table
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
            Resource.getReceptionPage(start, number, pageNumber, tableState, $scope.includedIps, sorting, search, ipSortString, $scope.columnFilters).then(function (result) {
                vm.displayedIps = result.data;
                tableState.pagination.numberOfPages = result.numberOfPages;//set the number of pages so the pagination can update
                $scope.ipLoading = false;
                $scope.initLoad = false;
            });
        }
    };
    $scope.tagsPlaceholder = function() {
        if (vm.request.tags.options.length == 0) {
            return "NO_TAGS";
        } else {
            return "SELECT_TAGS";
        }
    }
    //Click function for Ip table
    $scope.ipTableClick = function(row) {
        if($scope.select && $scope.ip.id == row.id){
            $scope.select = false;
            $scope.ip = null;
            $rootScope.ip = null;
            $scope.profileEditor = false;
        } else {
            $scope.profileEditor = true;
            $scope.select = true;
            $scope.ip = row;
            $rootScope.ip = $scope.ip;
            if($scope.filebrowser && !$scope.ip.url) {
                $scope.ip.url = appConfig.djangoUrl + "ip-reception/" + $scope.ip.id + "/";
            }
        }
    };
    $scope.filebrowser = false;
    $scope.filebrowserClick = function (ip) {
        if ($scope.filebrowser && $scope.ip == ip) {
            $scope.filebrowser = false;
            $scope.ip = null;
            $rootScope.ip = null;
            $scope.filebrowser = false;
        } else {
            $scope.filebrowser = true;
            if(!ip.url) {
                ip.url = appConfig.djangoUrl + "ip-reception/" + ip.id + "/";
            }
            $scope.ip = ip;
            $rootScope.ip = ip;
        }
    }

    //Reload current view
    $scope.reloadPage = function (){
        $state.reload();
    }
    $scope.yes = $translate.instant('YES');
    $scope.no = $translate.instant('NO');

    $scope.getArchivePolicies = function () {
        return ArchivePolicy.query()
            .$promise.then(function (data) {
                return data;
            });
    }
    $scope.getTags = function() {
        return Tag.query().$promise.then(function(data) {
            return data;
        });
    }
    $scope.receive = function(ips) {
        ips.forEach(function(ip) {
            Requests.receive(ip, vm.request, vm.validatorModel)
            .then(function(){
                $scope.getListViewData();
                $scope.eventlog = false;
                $scope.edit = false;
                $scope.requestForm = false;
                $scope.filebrowser = false;
                $scope.initRequestData();
            });
        });
    }

    //Create and show modal for remove ip
    $scope.receiveModal = function (ip) {
        if (ip.at_reception) {
            IPReception.get({ id: ip.id }).$promise.then(function (resource) {
                if(resource.altrecordids.SUBMISSIONAGREEMENT) {
                    IPReception.prepare({ id: resource.id, submission_agreement: resource.altrecordids.SUBMISSIONAGREEMENT[0] }).$promise.then(function(prepared) {
                        var modalInstance = $uibModal.open({
                            animation: true,
                            ariaLabelledBy: 'modal-title',
                            ariaDescribedBy: 'modal-body',
                            templateUrl: 'static/frontend/views/receive_modal.html',
                            controller: 'ReceiveModalInstanceCtrl',
                            size: "lg",
                            scope: $scope,
                            controllerAs: '$ctrl',
                            resolve: {
                                data: function () {
                                    return {
                                        ip: prepared,
                                        vm: vm
                                    };
                                }
                            },
                        })
                        modalInstance.result.then(function (data) {
                            $scope.getListViewData();
                            if (data.status == "received") {
                                $scope.eventlog = false;
                                $scope.edit = false;
                                $scope.requestForm = false;
                            }
                            $scope.filebrowser = false;
                            $scope.initRequestData();
                            $scope.includedIps.shift();
                            $scope.getListViewData();
                            if ($scope.includedIps.length > 0) {
                                $scope.getArchivePolicies().then(function (result) {
                                    vm.request.archivePolicy.options = result;
                                    $scope.getTags().then(function (result) {
                                        vm.request.tags.options = result;
                                        $scope.requestForm = true;
                                        $scope.receiveModal($scope.includedIps[0]);
                                    });
                                });
                            }
                        }, function () {
                            $log.info('modal-component dismissed at: ' + new Date());
                        });
                    })
                    .catch(function(response) {
                        var modalInstance = $uibModal.open({
                            animation: true,
                            ariaLabelledBy: 'modal-title',
                            ariaDescribedBy: 'modal-body',
                            templateUrl: 'static/frontend/views/receive_modal.html',
                            controller: 'ReceiveModalInstanceCtrl',
                            size: "lg",
                            scope: $scope,
                            controllerAs: '$ctrl',
                            resolve: {
                                data: function () {
                                    return {
                                        ip: resource,
                                        vm: vm
                                    };
                                }
                            },
                        })
                        modalInstance.result.then(function (data) {
                            $scope.getListViewData();
                            if (data.status == "received") {
                                $scope.eventlog = false;
                                $scope.edit = false;
                                $scope.requestForm = false;
                            }
                            $scope.filebrowser = false;
                            $scope.initRequestData();
                            $scope.includedIps.shift();
                            $scope.getListViewData();
                            if ($scope.includedIps.length > 0) {
                                $scope.getArchivePolicies().then(function (result) {
                                    vm.request.archivePolicy.options = result;
                                    $scope.getTags().then(function (result) {
                                        vm.request.tags.options = result;
                                        $scope.requestForm = true;
                                        $scope.receiveModal($scope.includedIps[0]);
                                    });
                                });
                            }
                        }, function () {
                            $log.info('modal-component dismissed at: ' + new Date());
                        });
                    })
                } else {
                    var modalInstance = $uibModal.open({
                        animation: true,
                        ariaLabelledBy: 'modal-title',
                        ariaDescribedBy: 'modal-body',
                        templateUrl: 'static/frontend/views/receive_modal.html',
                        controller: 'ReceiveModalInstanceCtrl',
                        size: "lg",
                        scope: $scope,
                        controllerAs: '$ctrl',
                        resolve: {
                            data: function () {
                                return {
                                    ip: resource,
                                    vm: vm
                                };
                            }
                        },
                    })
                    modalInstance.result.then(function (data) {
                        $scope.getListViewData();
                        if (data.status == "received") {
                            $scope.eventlog = false;
                            $scope.edit = false;
                            $scope.requestForm = false;
                        }
                        $scope.filebrowser = false;
                        $scope.initRequestData();
                        $scope.includedIps.shift();
                        $scope.getListViewData();
                        if ($scope.includedIps.length > 0) {
                            $scope.getArchivePolicies().then(function (result) {
                                vm.request.archivePolicy.options = result;
                                $scope.getTags().then(function (result) {
                                    vm.request.tags.options = result;
                                    $scope.requestForm = true;
                                    $scope.receiveModal($scope.includedIps[0]);
                                });
                            });
                        }
                    }, function () {
                        $log.info('modal-component dismissed at: ' + new Date());
                    });
                }
            })
        } else {
            IP.get({ id: ip.id }).$promise.then(function (resource) {
                var modalInstance = $uibModal.open({
                    animation: true,
                    ariaLabelledBy: 'modal-title',
                    ariaDescribedBy: 'modal-body',
                    templateUrl: 'static/frontend/views/receive_modal.html',
                    controller: 'ReceiveModalInstanceCtrl',
                    size: "lg",
                    scope: $scope,
                    controllerAs: '$ctrl',
                    resolve: {
                        data: function () {
                            return {
                                ip: resource,
                                vm: vm
                            };
                        }
                    },
                })
                modalInstance.result.then(function (data) {
                    $scope.getListViewData();
                    if (data.status == "received") {
                        $scope.eventlog = false;
                        $scope.edit = false;
                        $scope.requestForm = false;
                    }
                    $scope.filebrowser = false;
                    $scope.initRequestData();
                    $scope.includedIps.shift();
                    $scope.getListViewData();
                    if ($scope.includedIps.length > 0) {
                        $scope.getArchivePolicies().then(function (result) {
                            vm.request.archivePolicy.options = result;
                            $scope.getTags().then(function (result) {
                                vm.request.tags.options = result;
                                $scope.requestForm = true;
                                $scope.receiveModal($scope.includedIps[0]);
                            });
                        });
                    }
                }, function () {
                    $log.info('modal-component dismissed at: ' + new Date());
                });
            })
        }
    }

    $scope.informationClassAlert = null;
    $scope.alerts = {
        matchError: { type: 'danger', msg: $translate.instant('MATCH_ERROR') },
    };
    $scope.closeAlert = function() {
        $scope.informationClassAlert = null;
    }

    vm.uncheckAll = function() {
        $scope.includedIps = [];
        vm.displayedIps.forEach(function(row) {
            row.checked = false;
        });
    }

    $scope.clickSubmit = function() {
       if(vm.requestForm.$valid) {
           $scope.receive($scope.includedIps);
       }
    }
});
