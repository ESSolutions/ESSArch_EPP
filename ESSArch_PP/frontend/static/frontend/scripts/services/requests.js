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

angular.module('myApp').factory('Requests', function(Notifications, IPReception, IP, $http, appConfig) {
    function receive(ip, request, validators) {
        return IPReception.receive({
                id: ip.id,
                archive_policy: request.archivePolicy.value.id,
                purpose: request.purpose,
                tags: request.tags.value.map(function(tag){return tag.id}),
                allow_unknown_files: request.allowUnknownFiles,
                validators: validators,
        }).$promise.then(function(response) {
            Notifications.add(response.detail, "success", 3000);
            return response;
        }).catch(function(response) {
            if(response.status != 500 && response.data.detail) {
                Notifications.add(response.data.detail, "error");
            }
        })
    };
    function preserve(ip, request) {
        return IP.preserve(
            angular.extend(request, { id: ip.id })
        ).$promise.then(function (response) {
            Notifications.add(response.detail, "success", 3000);
            return response;
        }).catch(function(response) {
            Notifications.add(response.data.detail, "error");
        })
    }
    function access(ip, data) {
        return IP.access(angular.extend(data, { id: ip.id })).$promise.then(function(response) {
            Notifications.add(response.detail, "success", 3000);
            return response;
        }).catch(function(response) {
            Notifications.add(response.data.detail, "error");
        })
    }
    function moveToApproval(ip, data) {
        return IP.moveToApproval(angular.extend(data, { id: ip.id })).$promise.then(function(response) {
            Notifications.add(response.detail, "success", 3000);
            return response;
        }).catch(function(response) {
            Notifications.add(response.data.detail, "error");
        })
    }
    return {
        receive: receive,
        preserve: preserve,
        access: access,
        moveToApproval: moveToApproval,
    };
});
