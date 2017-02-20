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

angular.module('myApp').controller('AngularTreeCtrl', function AngularTreeCtrl($scope, $http, $rootScope, appConfig) {
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
});
