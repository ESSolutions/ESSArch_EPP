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

angular.module('myApp').factory('myService', function(Sysinfo, $location, PermPermissionStore, PermRoleStore, $anchorScroll, $http, appConfig, djangoAuth) {
    function changePath(state) {
        $state.go(state);
    };
    function getPermissions(permissions){
        PermPermissionStore.defineManyPermissions(permissions, /*@ngInject*/ function (permissionName) {
            return permissions.includes(permissionName);
        });
        return permissions;
    }

    function checkPermissions(permissions) {
        if (permissions.length == 0) {return true;}

        var hasPermissions = false;
        permissions.forEach(function(permission) {
            if(checkPermission(permission)) {
                hasPermissions = true;
            }
        });
        return hasPermissions;
    }

    function checkPermission(permission) {
        return !angular.isUndefined(PermPermissionStore.getPermissionDefinition(permission));
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
        return Sysinfo.get().$promise.then(function(data){
            return data;
        });
    }
    function getActiveColumns() {
        return djangoAuth.profile().then(function(response) {
            return generateColumns(response.data.ip_list_columns);
        });
    }
    function generateColumns(columns) {
        var allColumns = [
            { label: "object_identifier_value", sortString: "object_identifier_value", template: "static/frontend/views/columns/column_object_identifier_value.html" },
            { label: "label", sortString: "label", template: "static/frontend/views/columns/column_label.html" },
            { label: "responsible", sortString: "responsible", template: "static/frontend/views/columns/column_responsible.html" },
            { label: "create_date", sortString: "create_date", template: "static/frontend/views/columns/column_create_date.html" },
            { label: "state", sortString: "state", template: "static/frontend/views/columns/column_state.html" },
            { label: "step_state", sortString: "step_state", template: "static/frontend/views/columns/column_step_state.html" },
            { label: "events", sortString: "Events", template: "static/frontend/views/columns/column_events.html" },
            { label: "status", sortString: "status", template: "static/frontend/views/columns/column_status.html" },
            { label: "delete", sortString: "", template: "static/frontend/views/columns/column_delete.html" },
            { label: "object_size", sortString: "object_size", template: "static/frontend/views/columns/column_object_size.html" },
            { label: "archival_institution", sortString: "archival_institution", template: "static/frontend/views/columns/column_archival_institution.html" },
            { label: "archivist_organization", sortString: "archivist_organization", template: "static/frontend/views/columns/column_archivist_organization.html" },
            { label: "start_date", sortString: "start_date", template: "static/frontend/views/columns/column_start_date.html" },
            { label: "end_date", sortString: "end_date", template: "static/frontend/views/columns/column_end_date.html"},
            { label: "storage_status", sortString: "archived", template: "static/frontend/views/columns/column_storage_status.html"},
            { label: "filebrowser", sortString: "", template: "static/frontend/views/columns/column_filebrowser.html"},
            { label: "aic", sortString: "aic", template: "static/frontend/views/columns/column_aic.html" },
            { label: "entry_date", sortString: "entry_date", template: "static/frontend/views/columns/column_entry_date.html" },
        ];
        var activeColumns = allColumns.filter(function(c) {
            return columns.indexOf(c.label) >= 0;
        });
        return {activeColumns: activeColumns, allColumns: allColumns};
    }
    return {
        changePath: changePath,
        getPermissions: getPermissions,
        hasChild: hasChild,
        getVersionInfo: getVersionInfo,
        getActiveColumns: getActiveColumns,
        generateColumns: generateColumns,
        checkPermission: checkPermission,
        checkPermissions: checkPermissions,
    }
});
