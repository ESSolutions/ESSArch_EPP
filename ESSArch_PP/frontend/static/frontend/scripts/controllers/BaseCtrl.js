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

angular.module('myApp').controller('BaseCtrl', function ($log, $uibModal, $timeout, $scope, $window, $location, $sce, $http, myService, appConfig, $state, $stateParams, $rootScope, listViewService, $interval, Resource, $translate, $cookies, $cookieStore, $filter, $anchorScroll, PermPermissionStore, $q){
    vm = this;
    $scope.$state = $state;
    $scope.updateIpsPerPage = function(items) {
        $cookies.put('epp-ips-per-page', items);
    };
    $scope.colspan = 9;
    $scope.$window = $window;
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
        $http({
            method: 'POST',
            url: branch.url+"undo/"
        }).then(function(response) {
            $timeout(function(){
                $scope.statusViewUpdate($scope.ip);
            }, 1000);
        }, function() {
            console.log("error");
        });
    };
    //Redo step/task
    $scope.myTreeControl.scope.taskStepRedo = function(branch){
        $http({
            method: 'POST',
            url: branch.url+"retry/"
        }).then(function(response) {
            $timeout(function(){
                $scope.statusViewUpdate($scope.ip);
            }, 1000);
        }, function() {
            console.log("error");
        });
    };
    $scope.currentStepTask = {id: ""}
    $scope.myTreeControl.scope.updatePageNumber = function(branch, page) {
        if(page > branch.page_number && branch.next){
            branch.page_number = parseInt(branch.next.page);
            listViewService.getChildrenForStep(branch, branch.page_number);
        } else if(page < branch.page_number && branch.prev && page > 0) {
            branch.page_number = parseInt(branch.prev.page);
            listViewService.getChildrenForStep(branch, branch.page_number);
        }
    };

    //Click on +/- on step
    $scope.stepClick = function(step) {
        listViewService.getChildrenForStep(step);
    };

    //Click funciton for steps and tasks
    $scope.stepTaskClick = function(branch) {
        $http({
            method: 'GET',
            url: branch.url
        }).then(function(response){
            $scope.currentStepTask = response.data;
            if(branch.flow_type == "task"){
                $scope.taskInfoModal();
            } else {
                $scope.stepInfoModal();
            }
        }, function(response) {
            response.status;
        });
    };

    $scope.copyToClipboard = function() {
        $("#traceback_textarea").val($("#traceback_pre").html()).show();
        $("#traceback_pre").hide();
        $("#traceback_textarea").focus()[0].select();
        try {
            var successful = document.execCommand('copy');
            var msg = successful ? 'successful' : 'unsuccessful';
        } catch (err) {
            console.log('Oops, unable to copy');
        }
        $("#traceback_pre").html($("#traceback_textarea").val()).show();
        $("#traceback_textarea").hide();
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
    $scope.statusViewUpdate = function(row){
        $scope.statusLoading = true;
        var expandedNodes = [];
        if($scope.tree_data != []) {
            expandedNodes = checkExpanded($scope.tree_data);
        }
        listViewService.getTreeData(row, expandedNodes).then(function(value) {
            $scope.tree_data = value;
            $scope.statusLoading = false;
        }, function(response){
            if(response.status == 404) {
                $scope.statusShow = false;
                $timeout(function(){
                    $scope.getListViewData();
                }, 1000);
            }
        });
    };
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
            controllerAs: '$ctrl'
        })
        modalInstance.result.then(function (data) {
            $scope.removeIp(ipObject);
        }, function () {
            $log.info('modal-component dismissed at: ' + new Date());
        });
    }
    //advanced filter form data
    $scope.columnFilters = {};
    $scope.options = [];
    $scope.filterModels = [];
    $scope.filterFields = [];

    //Toggle visibility of advanced filters
    $scope.toggleAdvancedFilters = function () {
        if ($scope.showAdvancedFilters) {
            $scope.showAdvancedFilters = false;
        } else {
            if ($scope.filterModels.length === 0) {
                $scope.initAdvancedFilters();
            }
                $scope.showAdvancedFilters = true;
        }
        /* if ($scope.showAdvancedFilters) {
            console.log("set window click")
            $window.onclick = function (event) {
                closeSearchWhenClickingElsewhere(event, $scope.toggleAdvancedFilters);
            }
        } else {
            $scope.showAdvancedFilters = false;
            $scope.$window.onClick = null;
            $scope.$apply();
         }*/
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

    //Merge all filter models before fetching IP's
    $scope.createFilterObject = function () {
        $scope.filterModels.forEach(function (model) {
            if(model.filterField !== null) {
                $scope.columnFilters[model.column] = model.filterField;
            }
        });
    }

    //Reset variables for advanced fiters
    $scope.initAdvancedFilters = function () {
        $scope.columnFilters = {};
        $scope.filterModels = [getModelInput()];
        $scope.filterFields = [];
    }

    //Removes model on index in filter models
    $scope.removeForm = function($index) {
        if($scope.filterModels.length > 1) {
            delete $scope.columnFilters[$scope.filterModels[$index].column];
            if($index === 0) {
                $scope.filterModels[$index] = $scope.filterModels[$index+1];
                $scope.filterFields.splice($scope.filterFields.indexOf($scope.filterFields[$index])+1, 1);
                $scope.filterModels.splice($index+1, 1);
            } else {
                $scope.filterFields.splice($scope.filterFields.indexOf($scope.filterFields[$index]), 1);
                $scope.filterModels.splice($index, 1);
            }
        } else {
            $scope.initAdvancedFilters();
        }
    }

    //Get fields for every one model
    function getFields($index) {
        var allowedColumns = ["label", "object_identifier_value", "responsible", "create_date",
            "object_size", "archival_institution", "archivist_organization", "start_date", "end_date"];
        var columns = [];
        angular.copy($rootScope.listViewColumns).forEach(function (column) {
            if (allowedColumns.includes(column.label)) {
                column.label_translated = $translate.instant(column.label.toUpperCase());
                columns.push(column);
            }
        });
        var columnLabel = null;
        var filterLabel = null;

        if($index === 0) {
            columnLabel = $translate.instant("COLUMN");
            filterLabel = $translate.instant("FILTER");
        }
        return [
            {
                "templateOptions": {
                    "type": "text",
                    "label": columnLabel,
                    "labelProp": "label_translated",
                    "valueProp": "label",
                    "options": columns,
                },
                "type": "select",
                "key": "column",
            },
            {
                "templateOptions": {
                    "label": filterLabel,
                },
                "type": "input",
                "key": "filterField",
            },
        ];
    }

    //Add new field set to field array
    $scope.addFields = function ($index) {
        $scope.filterFields.push(new getFields($index));
    }

    //Get new empty model
    function getModelInput() {
        return {
            column: null,
            filterField: null
        }
    }
    //Add new row of model and fields (fields are genereated automatically)
    $scope.addFilterRow = function ($index) {
        $scope.filterModels.push(getModelInput());
    }
    $scope.submitAdvancedFilters = function() {
        $scope.createFilterObject();
        $scope.getListViewData();
    }
});
