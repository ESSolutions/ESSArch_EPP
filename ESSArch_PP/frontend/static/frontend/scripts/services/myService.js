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

angular.module('myApp').factory('myService', function($location, PermPermissionStore, $anchorScroll, $http, appConfig) {
    function changePath(state) {
        $state.go(state);
    };
    function getPermissions(permissions){
        PermPermissionStore.defineManyPermissions(permissions, /*@ngInject*/ function (permissionName) {
            return permissions.includes(permissionName);
        });
        return permissions;
    }
    function hasChild(node1, node2){
        var temp1 = false;
        if (node2.children) {
            node2.children.forEach(function(child) {
                if(node1.name == child.name) {
                    temp1 = true;
                }
                if(temp1 == false) {
                    temp1 = hasChild(node1, child);
                }
            });
        }
        return temp1;
    }
    function getVersionInfo() {
        return $http({
            method: 'GET',
            url: appConfig.djangoUrl+"sysinfo/"
        }).then(function(response){
            return response.data;
        }, function() {
            console.log('error');
        })
    }
    return {
        changePath: changePath,
        getPermissions: getPermissions,
        hasChild: hasChild,
        getVersionInfo: getVersionInfo
    }
});
