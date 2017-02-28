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

angular.module('myApp').controller('AngularTreeCtrl', function AngularTreeCtrl($scope, $http, $rootScope, appConfig, $translate, $uibModal, $log) {
    $scope.treeOptions = {
        nodeChildren: "children",
        dirSelectable: true,
        injectClasses: {
            ul: "a1",
            li: "a2",
            liSelected: "a7",
            iExpanded: "a3",
            iCollapsed: "a4",
            iLeaf: "a5",
            label: "a6",
            labelSelected: "a8"
        }
    }
    $scope.ArchivalInstitution = [
        {
            "name": "Archival institution",
            "children": []
        }
    ];

    $scope.ArchivistOrganization = [
        {
            "name": "Archivist organization",
            "children": []
        }
    ];

    /*
    $scope.ArchivalType = [
        {
            "name": "Archival type",
            "children": []
        }
    ];

    $scope.ArchivalLocation = [
       {
           "name": "Archival location",
           "children": []
        }
    ];
    */

    $scope.other = [
        {
            "name": "other",
            "children": []
        }
    ];

    $rootScope.loadNavigation = function(ipState) {
        $http({
            method: 'GET',
            url: appConfig.djangoUrl+"archival-institutions/",
            params: {ip_state: ipState}
        }).then(function(response) {
            $scope.ArchivalInstitution[0].children = response.data;
        });
        $http({
            method: 'GET',
            url: appConfig.djangoUrl+"archivist-organizations/",
            params: {ip_state: ipState}
        }).then(function(response) {
            $scope.ArchivistOrganization[0].children = response.data;
        });
       /* $http({
            method: 'GET',
            url: appConfig.djangoUrl+"archival-types/"
        }).then(function(response) {
            $scope.ArchivalType[0].children = response.data;
        });
        $http({
            method: 'GET',
            url: appConfig.djangoUrl+"archival-locations/"
        }).then(function(response) {
            $scope.ArchivalLocation[0].children = response.data;
        });*/
    }
    $rootScope.navigationFilter = {
        institution: null,
        organization: null,
        type: null,
        location: null,
        other: null
    };

    $scope.showSelectedInstitution = function(node) {
        $scope.nodeOther = null;
        $rootScope.navigationFilter.other = null;
        if(angular.isUndefined(node.id)){
            $rootScope.navigationFilter.institution = null;
            return;
        }
        if($rootScope.navigationFilter.institution == node.id){
            $rootScope.navigationFilter.institution = null;
        } else {
            $rootScope.navigationFilter.institution = node.id;
        }
    }

    $scope.showSelectedOrganization = function(node) {
        $scope.nodeOther = null;
        $rootScope.navigationFilter.other = null;
        if(angular.isUndefined(node.id)){
            $rootScope.navigationFilter.organization = null;
            return;
        }
        if($rootScope.navigationFilter.organization == node.id) {
            $rootScope.navigationFilter.organization = null;
        } else {
            $rootScope.navigationFilter.organization = node.id;
        }
    }

    $scope.showSelectedType = function(node) {
        $scope.nodeOther = null;
        $rootScope.navigationFilter.other = null;
        if(angular.isUndefined(node.id)){
            $rootScope.navigationFilter.type = null;
            return;
        }
        if($rootScope.navigationFilter.type == node.id) {
            $rootScope.navigationFilter.type = null;
        } else {
            $rootScope.navigationFilter.type = node.id;
        }
    }

    $scope.showSelectedLocation = function(node) {
        $scope.nodeOther = null;
        $rootScope.navigationFilter.other = null;
       if(angular.isUndefined(node.id)){
            $rootScope.navigationFilter.location = null;
            return;
        }
       if($rootScope.navigationFilter.location == node.id) {
            $rootScope.navigationFilter.location = null;
       } else {
            $rootScope.navigationFilter.location = node.id;
       }
    }

    $scope.showSelectedOther = function(node) {
        $scope.nodeInst = null;
        $scope.nodeOrg = null;
        $scope.nodeType = null;
        $scope.nodeLoc = null;
        if($rootScope.navigationFilter.other) {
            $rootScope.navigationFilter = {
                institution: null,
                organization: null,
                type: null,
                location: null,
                other: null
            };
        } else {
            $rootScope.navigationFilter = {
                institution: null,
                organization: null,
                type: null,
                location: null,
                other: true
            };
        }
    }

    //TAGS
    $scope.tags = [];
    $rootScope.loadTags = function() {
        $http({
            method: 'GET',
            url: appConfig.djangoUrl + 'tags/',
            params: {only_roots: true}
        }).then(function(response) {
            response.data.forEach(function(tag, index, array) {
                $scope.expandedNodes.forEach(function(node) {
                    if(tag.id == node.id) {
                        $scope.onNodeToggle(tag);
                    }
                });
            });
            $scope.tags = response.data;
        });
    }
    $rootScope.loadTags();
    $scope.onNodeToggle = function(node) {
        node.children.forEach(function(child, index, array) {
            $http({
                method: 'GET',
                url: child.url
            }).then(function(response) {
                array[index] = response.data;
            });
        });
    }
    $rootScope.ipUrl = null;
    $scope.showSelectedNode = function(node) {
        if($rootScope.ipUrl == node.url + 'information-packages/') {
            $rootScope.ipUrl = null;
        } else {
            $rootScope.ipUrl = node.url + 'information-packages/';
        }
    };
    // Remove given node
    $scope.removeNode = function(node) {
        if(node.parentNode == null){
            //$scope.treeElements.splice($scope.treeElements.indexOf(node.node), 1);
            return;
        }
        node.parentNode.children.forEach(function(element) {
            if(element.name == node.node.name) {
                node.parentNode.children.splice(node.parentNode.children.indexOf(element), 1);
                $http({
                    method: 'DELETE',
                    url: element.url
                }).then (function(response){});
            }
        });
    };
    //Update current node variable with selected node in map structure tree view
    $scope.updateCurrentNode = function(node, selected, parentNode) {
        if(selected) {
            $scope.currentNode = {"node": node, "parentNode": parentNode};
        } else {
            $scope.currentNode = null;
        }
    };
    //context menu data
    $scope.navMenuOptions = function(item) {
        return [
            [$translate.instant('ADD'), function ($itemScope, $event, modelValue, text, $li) {
                $scope.addTagModal($itemScope.node);
            }],

            [$translate.instant('REMOVE'), function ($itemScope, $event, modelValue, text, $li) {
                $scope.updateCurrentNode($itemScope.node, true, $itemScope.$parentNode);
                $scope.removeNode($scope.currentNode);
                $scope.selectedNode = null;
            }],
            [$translate.instant('UPDATE'), function ($itemScope, $event, modelValue, text, $li) {
                $scope.tagPropertiesModal($itemScope.node);
            }]
        ];
    };
    // open modal for add tag
    $scope.addTagModal = function (tag) {
        var modalInstance = $uibModal.open({
            animation: true,
            ariaLabelledBy: 'modal-title',
            ariaDescribedBy: 'modal-body',
            templateUrl: 'static/frontend/views/add_tag_modal.html',
            scope: $scope,
            controller: 'ModalInstanceCtrl',
            controllerAs: '$ctrl'
        })
        modalInstance.result.then(function (data) {
            $scope.addTag(tag, data);
        }, function () {
            $log.info('modal-component dismissed at: ' + new Date());
        });
    }
    // Add new tag
    $scope.addTag = function(tag, data) {
        data.parent = tag.url;
        data.information_packages = [];
        if(tag == null){
            $scope.tags[0].children.push(dir);
        } else {
            $http({
                method: 'POST',
                url: appConfig.djangoUrl + 'tags/',
                data: data
            }).then(function(response) {
                tag.children.push(response.data);
            });
        }
    };
    $scope.tagPropertiesModal = function (tag) {
        $scope.displayedTag = tag;
        var modalInstance = $uibModal.open({
            animation: true,
            ariaLabelledBy: 'modal-title',
            ariaDescribedBy: 'modal-body',
            templateUrl: 'static/frontend/views/tag_properties_modal.html',
            scope: $scope,
            controller: 'ModalInstanceCtrl',
            controllerAs: '$ctrl'
        })
        modalInstance.result.then(function (data) {
            $http({
                method: 'PATCH',
                url: tag.url,
                data: data
            }).then(function(response) {
                $rootScope.loadTags();
            });
        }, function () {
            $log.info('modal-component dismissed at: ' + new Date());
        });
    }
});
