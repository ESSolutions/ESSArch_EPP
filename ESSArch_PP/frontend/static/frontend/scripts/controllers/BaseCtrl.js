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

angular.module('myApp').controller('BaseCtrl',  function(IP, Task, Step, vm, ipSortString, $log, $uibModal, $timeout, $scope, $window, $location, $sce, $http, myService, appConfig, $state, $stateParams, $rootScope, listViewService, $interval, Resource, $translate, $cookies, $cookieStore, $filter, $anchorScroll, PermPermissionStore, $q, Requests){
    // Initialize variables

    $scope.$window = $window;
    $scope.$state = $state;
    vm.options = {};
    $scope.max = 100;
    $scope.stepTaskInfoShow = false;
    $scope.statusShow = false;
    $scope.eventShow = false;
    $scope.select = false;
    $scope.subSelect = false;
    $scope.edit = false;
    $scope.eventlog = false;
    $scope.requestForm = false;
    $scope.filebrowser = false;
    $scope.ip = null;
    $rootScope.ip = null;
    vm.itemsPerPage = $cookies.get('epp-ips-per-page') || 10;
    vm.ipViewType = $cookies.get('ip-view-type') || 1;
    vm.archived = false;

    // Init request form

    //Request form data
    $scope.initRequestData = function () {
        vm.request = {
            type: "",
            purpose: "",
            storageMedium: {
                value: "",
                options: ["Disk", "Tape(type1)", "Tape(type2)"]
            }
        };
    }
    $scope.initRequestData();

    // Watchers
    $rootScope.$watch(function () { return $rootScope.selectedTag; }, function (newVal, oldVal) {
        $scope.getListViewData();
    }, true);

    // Initialize intervals

    //Cancel update intervals on state change
    $rootScope.$on('$stateChangeStart', function() {
        $interval.cancel(stateInterval);
        $interval.cancel(listViewInterval);
    });

    var stateInterval;
    //If status view is visible, start update interval
    $scope.$watch(function(){return $scope.statusShow;}, function(newValue, oldValue) {
        if(newValue) {
            $interval.cancel(stateInterval);
            stateInterval = $interval(function(){$scope.statusViewUpdate($scope.ip)}, appConfig.stateInterval);
        } else {
            $interval.cancel(stateInterval);
        }
    });

    // list view update interval

    //Update ip list view with an interval
    //Update only if status < 100 and no step has failed in any IP
    var listViewInterval;
    vm.updateListViewConditional = function() {
        $interval.cancel(listViewInterval);
        listViewInterval = $interval(function() {
            var updateVar = false;
            vm.displayedIps.forEach(function(ip, idx) {
                if(ip.status < 100) {
                    if(ip.step_state != "FAILURE") {
                        updateVar = true;
                    }
                }
            });
            if(updateVar) {
                $scope.getListViewData();
            } else {
                $interval.cancel(listViewInterval);
                listViewInterval = $interval(function() {
                    var updateVar = false;
                    vm.displayedIps.forEach(function(ip, idx) {
                        if(ip.status < 100) {
                            if(ip.step_state != "FAILURE") {
                                updateVar = true;
                            }
                        }
                    });
                    if(!updateVar) {
                        $scope.getListViewData();
                    } else {
                        vm.updateListViewConditional();
                    }

                }, appConfig.ipIdleInterval);
            }
        }, appConfig.ipInterval);
    };
    vm.updateListViewConditional();

    // Click fucntions

    //Click function for status view
    $scope.stateClicked = function (row) {
        if ($scope.statusShow) {
                $scope.tree_data = [];
            if ($scope.ip == row) {
                $scope.statusShow = false;
                if(!$scope.select && !$scope.edit && !$scope.statusShow && !$scope.eventShow && !$scope.requestForm && !$scope.filebrowser) {
                    $scope.ip = null;
                    $rootScope.ip = null;
                }
            } else {
                $scope.statusShow = true;
                $scope.edit = false;
                $scope.statusViewUpdate(row);
                $scope.ip = row;
                $rootScope.ip = row;
            }
        } else {
            $scope.statusShow = true;
            $scope.edit = false;
            $scope.statusViewUpdate(row);
            $scope.ip = row;
            $rootScope.ip = row;
        }
        $scope.subSelect = false;
        $scope.eventlog = false;
        $scope.select = false;
        $scope.requestForm = false;
        $scope.eventShow = false;
    };

    //Click funciton for event view
    $scope.eventsClick = function (row) {
        if($scope.eventShow && $scope.ip == row){
            $scope.eventShow = false;
            $rootScope.stCtrl = null;
            if(!$scope.select && !$scope.edit && !$scope.statusShow && !$scope.eventShow && !$scope.requestForm && !$scope.filebrowser) {
                $scope.ip = null;
                $rootScope.ip = null;
            }
        } else {
            $scope.eventShow = true;
            $scope.statusShow = false;
            $scope.ip = row;
            $rootScope.ip = row;
        }
    };

    $scope.filebrowserClick = function (ip) {
        if ($scope.filebrowser && $scope.ip == ip) {
            $scope.filebrowser = false;
            if(!$scope.select && !$scope.edit && !$scope.statusShow && !$scope.eventShow && !$scope.requestForm && !$scope.filebrowser) {
                $scope.ip = null;
                $rootScope.ip = null;
            }
        } else {
            if ($rootScope.auth.id == ip.responsible.id || !ip.responsible) {
                $scope.filebrowser = true;
                $scope.ip = ip;
                $rootScope.ip = ip;
            }
        }
    }

    // List view

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
            Resource.getIpPage(start, number, pageNumber, tableState, sorting, search, ipSortString, $scope.expandedAics, $scope.columnFilters, vm.archived, vm.workarea).then(function (result) {
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

    //Get data for list view
    $scope.getListViewData = function() {
        vm.callServer($scope.tableState);
        $rootScope.$broadcast('load_tags', {})
    };

    // Validators

    vm.validatorModel = {
    };
    vm.validatorFields = [
    {
        "templateOptions": {
            "label": $translate.instant('VALIDATEFILEFORMAT'),
        },
        "defaultValue": true,
        "type": "checkbox",
        "key": "validate_file_format",
    },
    {
        "templateOptions": {
            "label": $translate.instant('VALIDATEXMLFILE'),
        },
        "defaultValue": true,
        "type": "checkbox",
        "key": "validate_xml_file",
    },
    {
        "templateOptions": {
            "label": $translate.instant('VALIDATELOGICALPHYSICALREPRESENTATION'),
        },
        "defaultValue": true,
        "type": "checkbox",
        "key": "validate_logical_physical_representation",
    },
    {
        "templateOptions": {
            "label": $translate.instant('VALIDATEINTEGRITY'),
        },
        "defaultValue": true,
        "type": "checkbox",
        "key": "validate_integrity",
    }
    ];

    // Requests
    $scope.submitRequest = function(ip, request) {
        switch(request.type) {
            case "preserve":
                $scope.preserveIp(ip, request);
                break;
            case "get":
                $scope.accessIp(ip, request);
                break;
            case "get_tar":
                $scope.accessIp(ip, request);
                break;
            case "get_as_new":
                $scope.accessIp(ip, request);
                break;
            case "move_to_approval":
                $scope.moveToApproval(ip, request);
                break;
            case "diff_check":
                console.log("request not implemented");
                break;
            default:
                console.log("request not matched");
                break;
        }
    }

    // Preserve IP
    $scope.preserveIp = function(ip, request) {
        var params = { purpose: request.purpose };
        params.policy =  request.archivePolicy && request.archivePolicy.value != "" ? request.archivePolicy.value.id : null;
        Requests.preserve(ip, params).then(function(result) {
            $scope.requestForm = false;
            $scope.eventlog = false;
            $scope.requestEventlog = false;
            $scope.filebrowser = false;
            $scope.eventShow = false;
            $scope.statusShow = false;
            $scope.initRequestData();
            $scope.getListViewData();
        });
    }

    $scope.accessIp = function(ip, request) {
        var data = { purpose: request.purpose, tar: request.type === "get_tar", extracted: request.type === "get", new: request.type === "get_as_new", package_xml: request.package_xml, aic_xml: request.aic_xml};
        Requests.access(ip, data).then(function(response) {
            $scope.requestForm = false;
            $scope.eventlog = false;
            $scope.requestEventlog = false;
            $scope.filebrowser = false;
            $scope.edit = false;
            $scope.select = false;
            $scope.eventShow = false;
            $scope.statusShow = false;
            $scope.initRequestData();
            $timeout(function() {
                $scope.ip = null;
                $rootScope.ip = null;
                $scope.getListViewData();
            });
        });
    }

    $scope.moveToApproval = function(ip, request) {
        var data = { purpose: request.purpose };
        Requests.moveToApproval(ip, data).then(function(response) {
            $scope.requestForm = false;
            $scope.eventlog = false;
            $scope.requestEventlog = false;
            $scope.eventShow = false;
            $scope.filebrowser = false;
            $scope.edit = false;
            $scope.select = false;
            $scope.eventShow = false;
            $scope.statusShow = false;
            $scope.initRequestData();
            $timeout(function() {
                $scope.ip = null;
                $rootScope.ip = null;
                $scope.getListViewData();
            });
        });
    }

    // Basic functions

    //Adds a new event to the database
    $scope.addEvent = function(ip, eventType, eventDetail) {
        listViewService.addEvent(ip, eventType, eventDetail).then(function(value) {
        });
    }

    //Functions for extended filters
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
    $scope.clearSearch = function() {
            delete $scope.tableState.search.predicateObject;
            $('#search-input')[0].value = "";
            $scope.getListViewData();
    }

    // AIC's
    $scope.expandedAics = [];
	$scope.expandAic = function(row) {
		row.collapsed = !row.collapsed;
		if(!row.collapsed) {
			$scope.expandedAics.push(row.object_identifier_value);
		} else {
			$scope.expandedAics.forEach(function(aic, index, array) {
				if(aic == row.object_identifier_value) {
					$scope.expandedAics.splice(index,1);
				}
			});
		};
    }

    // Expand all IP's
    vm.expandAll = function() {
        vm.displayedIps.forEach(function(ip) {
            ip.collapsed = false;
			$scope.expandedAics.push(ip.object_identifier_value);
        })
    }

    vm.collapseAll = function() {
        vm.displayedIps.forEach(function(ip) {
            ip.collapsed = true;
            $scope.expandedAics.forEach(function(aic, index, array) {
				if(aic == ip.object_identifier_value) {
					$scope.expandedAics.splice(index,1);
				}
			});
        })
    }

    vm.expandAllVisible = function() {
        var visible = false;
        var expand = true;
        vm.displayedIps.forEach(function(ip) {
            if(ip.information_packages && ip.information_packages.length) {
                visible = true;
                if(ip.collapsed == false) {
                    expand = false;
                }
            }
        })
        vm.showExpand = expand;
        return visible;
    }
    // Remove ip
	$scope.removeIp = function (ipObject) {
		IP.delete({
			id: ipObject.id
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

    //Get data for eventlog view
    vm.getEventlogData = function() {
        listViewService.getEventlogData().then(function(value){
            $scope.eventTypeCollection = value;
        });
    };

    $scope.updateIpsPerPage = function(items) {
        $cookies.put('epp-ips-per-page', items);
    };
    $scope.menuOptions = [];
    //Status tree view structure
    $scope.tree_data = [];
    $scope.angular = angular;
    $scope.statusShow = false;
    $scope.eventShow = false;
    $translate(['LABEL', 'RESPONSIBLE', 'DATE', 'STATE', 'STATUS']).then(function(translations) {
        $scope.responsible = translations.RESPONSIBLE;
        $scope.label = translations.LABEL;
        $scope.date = translations.DATE;
        $scope.state = translations.STATE;
        $scope.status = translations.STATUS;
        $scope.expanding_property = {
            field: "name",
            displayName: $scope.label,
        };
        $scope.col_defs = [
            {
                field: "user",
                displayName: $scope.responsible
            },
            {
                cellTemplate: "<div ng-include src=\"'static/frontend/views/task_pagination.html'\"></div>"
            },
            {
                field: "time_started",
                displayName: $scope.date

            },
            {
                field: "status",
                displayName: $scope.state,
                cellTemplate: "<div ng-if=\"row.branch[col.field] == 'SUCCESS'\" class=\"step-state-success\"><b>{{'SUCCESS' | translate}}</b></div><div ng-if=\"row.branch[col.field] == 'FAILURE'\" class=\"step-state-failure\"><b>{{'FAILURE' | translate}}</b></div><div ng-if=\"row.branch[col.field] != 'SUCCESS' && row.branch[col.field] !='FAILURE'\" class=\"step-state-in-progress\"><b>{{'INPROGRESS' | translate}}</b></div>"

            },
            {
                field: "progress",
                displayName: $scope.status,
                cellTemplate: "<uib-progressbar class=\"progress\" value=\"row.branch[col.field]\" type=\"success\"><b>{{row.branch[col.field]+\"%\"}}</b></uib-progressbar>"
            }
        ];
        if($scope.checkPermission("WorkflowEngine.can_undo") || $scope.checkPermission("WorkflowEngine.can_retry")) {
            $scope.col_defs.push(
            {
                cellTemplate: "<div ng-include src=\"'static/frontend/views/undo_redo.html'\"></div>"
            });
        }
    });
    $scope.myTreeControl = {};
    $scope.myTreeControl.scope = this;
    //Undo step/task
    $scope.myTreeControl.scope.taskStepUndo = function(branch) {
        branch.$undo().then(function(response) {
            $timeout(function(){
                $scope.statusViewUpdate($scope.ip);
            }, 1000);
        }).catch(function() {
            console.log("error");
        });
    };
    //Redo step/task
    $scope.myTreeControl.scope.taskStepRedo = function(branch){
        branch.$retry().then(function(response) {
            $timeout(function(){
                $scope.statusViewUpdate($scope.ip);
            }, 1000);
        }).catch(function() {
            console.log("error");
        });
    };
    $scope.currentStepTask = {id: ""}
    $scope.myTreeControl.scope.updatePageNumber = function(branch, page) {
        if(page > branch.page_number && branch.next){
            branch.page_number = parseInt(branch.next.page);
            listViewService.getChildrenForStep(branch, branch.page_number).then(function(result) {
                branch = result;
            })
        } else if(page < branch.page_number && branch.prev && page > 0) {
            branch.page_number = parseInt(branch.prev.page);
            listViewService.getChildrenForStep(branch, branch.page_number).then(function(result) {
                branch = result;
            })
        }
    };

    //Click on +/- on step
    $scope.stepClick = function(step) {
        listViewService.getChildrenForStep(step);
    };

    $scope.getTask = function(branch) {
        return Task.get({ id: branch.id }).$promise.then(function (data) {
            var started = moment(data.time_started);
            var done = moment(data.time_done);
            data.duration = done.diff(started);
            $scope.currentStepTask = data;
            $scope.stepTaskLoading = false;
            return data;
        });
    }

    $scope.getStep = function(branch) {
        return Step.get({ id: branch.id }).$promise.then(function (data) {
            var started = moment(data.time_started);
            var done = moment(data.time_done);
            data.duration = done.diff(started);
            $scope.currentStepTask = data;
            $scope.stepTaskLoading = false;
            return data;
        });
    }
    //Click funciton for steps and tasks
    $scope.stepTaskClick = function (branch) {
        $scope.stepTaskLoading = true;
        if (branch.flow_type == "task") {
            $scope.getTask(branch).then(function(data) {
                $scope.taskInfoModal();
            });
        } else {
            $scope.getStep(branch).then(function(data) {
                $scope.stepInfoModal();
            });
        }
    };

    //Redirect to admin page
    $scope.redirectAdmin = function () {
        $window.location.href="/admin/";
    }
    $scope.checkPermission = function(permissionName) {
        return !angular.isUndefined(PermPermissionStore.getPermissionDefinition(permissionName));
    };
    $scope.extendedEqual = function(specification_data, model) {
        var returnValue = true;
        for(var prop in model) {
            if(model[prop] == "" && angular.isUndefined(specification_data[prop])){
                returnValue = false;
            }
        }
        if(returnValue) {
            return angular.equals(specification_data, model);
        } else {
            return true;
        }
    };

    //Update status view data
    $scope.statusViewUpdate = function (row) {
        $scope.statusLoading = true;
        var expandedNodes = [];
        if ($scope.tree_data != []) {
            expandedNodes = checkExpanded($scope.tree_data);
        }
        listViewService.getTreeData(row, expandedNodes).then(function (value) {
            $q.all(value).then(function (values) {
                if ($scope.tree_data.length) {
                    $scope.tree_data = updateStepProperties($scope.tree_data, values);
                } else {
                    $scope.tree_data = value;
                }
            })
            $scope.statusLoading = false;
        }, function (response) {
            if (response.status == 404) {
                $scope.statusShow = false;
                $timeout(function () {
                    $scope.getListViewData();
                    updateListViewConditional();
                }, 1000);
            }
        });
    };

    // Calculates difference in two sets of steps and tasks recursively
    // and updates the old set with the differances.
    function updateStepProperties(A, B) {
        if (A.length > B.length) {
            A.splice(0, B.length);
        }
        for (i = 0; i < B.length; i++) {
            if (A[i]) {
                for (var prop in B[i]) {
                    if (B[i].hasOwnProperty(prop) && prop != "children") {
                        A[i][prop] = compareAndReplace(A[i], B[i], prop);
                    }
                }
                if (B[i].flow_type != "task") {
                    waitForChildren(A[i], B[i]).then(function (result) {
                        result.step.children = result.children;
                    })
                }
            } else {
                A.push(B[i]);
            }
        }
        return A;
    }

    // Waits for promises in b.children to resolve before returning
    // the result from updateStepProperties called with children of a and b
    function waitForChildren(a, b) {
        return $q.all(b.children).then(function (bchildren) {
            return { step: a, children: updateStepProperties(a.children, bchildren) };
        })
    }
    // If property in a and b does not have the same value, update a with the value of b
    function compareAndReplace(a, b, prop) {
        if (a.hasOwnProperty(prop) && b.hasOwnProperty(prop)) {
            if (a[prop] !== b[prop]) {
                a[prop] = b[prop];
            }
            return a[prop];
        } else {
            return b[prop]
        }
    }
    //checks expanded rows in tree structure
    function checkExpanded(nodes) {
        var ret = [];
        nodes.forEach(function(node) {
            if(node.expanded == true) {
                ret.push(node);
            }
            if(node.children && node.children.length > 0) {
                ret = ret.concat(checkExpanded(node.children));
            }
        });
        return ret;
    }

    //Modal functions
    $scope.tracebackModal = function (profiles) {
        $scope.profileToSave = profiles;
        var modalInstance = $uibModal.open({
            animation: true,
            ariaLabelledBy: 'modal-title',
            ariaDescribedBy: 'modal-body',
            templateUrl: 'static/frontend/views/task_traceback_modal.html',
            scope: $scope,
            size: 'lg',
            controller: 'ModalInstanceCtrl',
            controllerAs: '$ctrl'
        })
        modalInstance.result.then(function (data) {
        }, function () {
            $log.info('modal-component dismissed at: ' + new Date());
        });
    }
    //Creates and shows modal with task information
    $scope.taskInfoModal = function () {
        var modalInstance = $uibModal.open({
            animation: true,
            ariaLabelledBy: 'modal-title',
            ariaDescribedBy: 'modal-body',
            templateUrl: 'static/frontend/views/task_info_modal.html',
            scope: $scope,
            controller: 'ModalInstanceCtrl',
            controllerAs: '$ctrl'
        });
        modalInstance.result.then(function (data, $ctrl) {
        }, function () {
            $log.info('modal-component dismissed at: ' + new Date());
        });
    }
    //Creates and shows modal with step information
    $scope.stepInfoModal = function () {
        var modalInstance = $uibModal.open({
            animation: true,
            ariaLabelledBy: 'modal-title',
            ariaDescribedBy: 'modal-body',
            templateUrl: 'static/frontend/views/step_info_modal.html',
            scope: $scope,
            controller: 'ModalInstanceCtrl',
            controllerAs: '$ctrl'
        });
        modalInstance.result.then(function (data, $ctrl) {
        }, function () {
            $log.info('modal-component dismissed at: ' + new Date());
        });
    }
    //Create and show modal for remove ip
    $scope.removeIpModal = function (ipObject) {
        var modalInstance = $uibModal.open({
            animation: true,
            ariaLabelledBy: 'modal-title',
            ariaDescribedBy: 'modal-body',
            templateUrl: 'static/frontend/views/remove-ip-modal.html',
            controller: 'ModalInstanceCtrl',
            controllerAs: '$ctrl',
            resolve: {
                data: function () {
                    return {
                        ip: ipObject,
                    };
                }
            },
        })
        modalInstance.result.then(function (data) {
            $scope.removeIp(ipObject);
        }, function () {
            $log.info('modal-component dismissed at: ' + new Date());
        });
    }

    //advanced filter form data
    $scope.columnFilters = {};
    $scope.filterModel = {};
    $scope.options = {};
    $scope.fields = [];
    vm.setupForm = function() {
        $scope.fields = [];
        $scope.filterModel = {};
        for (var key in $scope.usedColumns) {
            var column = $scope.usedColumns[key];
            switch (column.type) {
                case "ModelChoiceFilter":
                case "ChoiceFilter":
                    $scope.fields.push({
                        "templateOptions": {
                            "type": "text",
                            "label": $translate.instant(key.toUpperCase()),
                            "labelProp": "display_name",
                            "valueProp": "value",
                            "options": column.choices,
                        },
                        "type": "select",
                        "key": key,
                    })
                    break;
                case "BooleanFilter":
                    $scope.fields.push({
                        "templateOptions": {
                            "label": $translate.instant(key.toUpperCase()),
                            "labelProp": key,
                            "valueProp": key,
                        },
                        "type": "checkbox",
                        "key": key,
                    })
                    break;
                case "ListFilter":
                case "CharFilter":
                    $scope.fields.push({
                        "templateOptions": {
                            "type": "text",
                            "label": $translate.instant(key.toUpperCase()),
                            "labelProp": key,
                            "valueProp": key,
                        },
                        "type": "input",
                        "key": key,
                    })
                    break;
                case "IsoDateTimeFromToRangeFilter":
                    $scope.fields.push(
                        {
                            "templateOptions": {
                                "type": "text",
                                "label": $translate.instant(key.toUpperCase() + "_START"),
                            },
                            "type": "datepicker",
                            "key": key + "_0"
                        }
                    )
                    $scope.fields.push(
                        {
                            "templateOptions": {
                                "type": "text",
                                "label": $translate.instant(key.toUpperCase() + "_END"),
                            },
                            "type": "datepicker",
                            "key": key + "_1"
                        }
                    )
                    break;
            }
        }
    }

    vm.toggleOwnIps = function(filterIps) {
        if(filterIps) {
            $scope.filterModel.responsible = $rootScope.auth.username;
        } else {
            if($scope.filterModel.responsible == $rootScope.auth.username) {
                delete $scope.filterModel.responsible;
            }
        }
    }

    //Toggle visibility of advanced filters
    $scope.toggleAdvancedFilters = function () {
        if ($scope.showAdvancedFilters) {
            $scope.showAdvancedFilters = false;
        } else {
            if ($scope.fields.length <=0) {
                $http({
                    method: "OPTIONS",
                    url: appConfig.djangoUrl + "information-packages/"
                }).then(function(response) {
                    $scope.usedColumns = response.data.filters;
                    vm.setupForm();
                });
            }
            $scope.showAdvancedFilters = true;
        }
         if ($scope.showAdvancedFilters) {
             $window.onclick = function (event) {
                 var clickedElement = $(event.target);
                 if (!clickedElement) return;
                 var elementClasses = event.target.classList;
                 var clickedOnAdvancedFilters = elementClasses.contains('filter-icon') ||
                 elementClasses.contains('advanced-filters') ||
                 clickedElement.parents('.advanced-filters').length ||
                 clickedElement.parents('.button-group').length;

                 if (!clickedOnAdvancedFilters) {
                     $scope.showAdvancedFilters = !$scope.showAdvancedFilters;
                     $window.onclick = null;
                     $scope.$apply();
                 }
             }
         } else {
             $window.onclick = null;
         }
    }

    $scope.clearSearch = function() {
        delete $scope.tableState.search.predicateObject;
        $('#search-input')[0].value = "";
        $scope.getListViewData();
    }

    $scope.filterActive = function() {
        var temp = false;
        for(var key in $scope.columnFilters) {
            if($scope.columnFilters[key] !== "" && $scope.columnFilters[key] !== null) {
                temp = true;
            }
        }
        return temp;
    }

    $scope.submitAdvancedFilters = function() {
        $scope.columnFilters = angular.copy($scope.filterModel);
        $scope.getListViewData();
    }

    // Click function for request form submit.
    // Replaced form="vm.requestForm" to work in IE
    $scope.clickSubmit = function () {
        if (vm.requestForm.$valid) {
            $scope.submitRequest($scope.ip, vm.request);
        }
    }
});
