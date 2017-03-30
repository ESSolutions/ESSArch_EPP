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

angular.module('myApp').factory('myService', function($location, PermPermissionStore, $anchorScroll, $http, appConfig, djangoAuth) {
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
    function getActiveColumns() {
        return djangoAuth.profile().then(function(response) {
            return generateColumns(response.data.ip_list_columns);
        });
    }
    function generateColumns(columns) {
        var allColumns = [{label: "object_identifier_value", sortString: "ObjectIdentifierValue", template: "static/frontend/views/columns/column_object_identifier_value.html"}, {label: "label", sortString: "Label", template: "static/frontend/views/columns/column_label.html"}, {label: "responsible", sortString: "Responsible", template: "static/frontend/views/columns/column_responsible.html"}, {label: "create_date", sortString: "CreateDate", template: "static/frontend/views/columns/column_create_date.html"}, {label: "state", sortString: "State", template: "static/frontend/views/columns/column_state.html"}, {label: "step_state", sortString: "step_state", template: "static/frontend/views/columns/column_step_state.html"}, {label: "events", sortString: "Events", template: "static/frontend/views/columns/column_events.html"}, {label: "status", sortString: "Status", template: "static/frontend/views/columns/column_status.html"}, {label: "delete", sortString: "", template: "static/frontend/views/columns/column_delete.html"}, {label: "object_size", sortString: "object_size", template: "static/frontend/views/columns/column_object_size.html"}, {label: "archival_institution", sortString: "ArchivalInstitution", template: "static/frontend/views/columns/column_archival_institution.html"}, {label: "archivist_organization", sortString: "ArchivistOrganization", template: "static/frontend/views/columns/column_archivist_organization.html"}, {label: "start_date", sortString: "Startdate", template: "static/frontend/views/columns/column_start_date.html"}, {label: "end_date", sortString: "Enddate", template: "static/frontend/views/columns/column_end_date.html"}];
        var activeColumns = [];
        var simpleColumns = allColumns.map(function(a){return a.label});
        columns.forEach(function(column) {
            for(i=0; i < simpleColumns.length; i++) {
                if(column === simpleColumns[i]) {
                    activeColumns.push(allColumns[i]);
                }
            }
        });
        return {activeColumns: activeColumns, allColumns: allColumns};
    }
    return {
        changePath: changePath,
        getPermissions: getPermissions,
        hasChild: hasChild,
        getVersionInfo: getVersionInfo,
        getActiveColumns: getActiveColumns,
        generateColumns: generateColumns
    }
});
