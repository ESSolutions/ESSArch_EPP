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

angular.module('myApp').factory('Requests', function($http, appConfig) {
    function receive(ip, request, validators) {
        console.log(request);
        return $http({
            method: 'POST',
            url: appConfig.djangoUrl + 'ip-reception/' + ip.id + '/receive/',
            data: {
                archive_policy: request.archivePolicy.value.id,
                submission_agreement: request.submissionAgreement.value,
                purpose: request.purpose,
                tags: request.tags.value.map(function(tag){return tag.id}),
                profile_data: request.profileData,
                allow_unknown_files: request.allowUnknownFiles,
                validators: validators,
            }
        }).then(function(response) {
            return response;
        });
    };
    function preserve(ip, request) {
        return $http({
            method: 'POST',
            url: ip.url + 'preserve/',
            data: request
        }).then(function (response) {
            return response;
        });
    }
    function access(ip, data) {
        return $http.post(ip.url + "access/", data).then(function(response) {
            return response;
        });
    }
    return {
        receive: receive,
        preserve: preserve,
        access: access,
    };
});