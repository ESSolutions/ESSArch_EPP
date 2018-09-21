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

'use strict';

describe('ReceptionCtrl', function() {
    beforeEach(module('myApp'));
    window.onbeforeunload = jasmine.createSpy();

    var $controller, $scope;

    beforeEach(inject(function(_$controller_){
        $controller = _$controller_;
    }));

    describe('toggling', function() {
        var $scope, controller;

        beforeEach(inject(function($rootScope){
            $scope = $rootScope.$new();
            controller = $controller('ReceptionCtrl', { $scope: $scope });
            $scope.ip = {
                "url": "http://localhost:8000/api/information-packages/b76e97e8-2896-47a5-87df-da740dff7535/",
                "id": "b76e97e8-2896-47a5-87df-da740dff7535",
                "label": "test18911_1",
                "object_identifier_value": "test18911_1",
                "object_size": 38594892,
                "object_path": "/ESSArch/data/etp/reception/test18911_1.tar",
                "submission_agreement": "5672f6b9-bbe0-4ea2-8b1b-1cf527f7c936",
                "submission_agreement_locked": true,
                "package_type": 0,
                "package_type_display": "SIP",
                "responsible": {
                    "id": 4,
                    "username": "admin",
                },
                "create_date": "2018-09-11T13:44:20.799253+02:00",
                "object_num_items": 45,
                "entry_date": "2018-09-11T13:44:20.799253+02:00",
                "state": "Created",
                "status": 100,
                "step_state": "SUCCESS",
                "policy": null,
                "message_digest": "",
                "message_digest_algorithm": null,
                "content_mets_create_date": "2018-09-11T13:45:22.188677+02:00",
                "content_mets_size": 24958,
                "content_mets_digest_algorithm": 3,
                "content_mets_digest": "70a4b01e5c5878265cb8f6d16c423f87f5c95f665bca2950d23edc59ca088967",
                "package_mets_create_date": null,
                "package_mets_size": null,
                "package_mets_digest_algorithm": null,
                "package_mets_digest": "",
                "start_date": "2016-11-10T00:00:00+01:00",
                "end_date": "2016-12-20T00:00:00+01:00",
                "permissions": [
                    "submit_sip",
                    "can_upload",
                    "set_uploaded",
                    "view_informationpackage",
                    "add_submissionagreement",
                    "prepare_ip",
                    "delete_informationpackage",
                    "create_sip"
                ],
                "appraisal_date": null,
            }
        }));

        describe('$scope.closeAlert', function() {
            it('on init informationClassAlert should be null', function() {
                expect($scope.informationClassAlert).toBe(null);
            });

            it('after calling closeAlert() informationClassAlert should be null', function() {
                $scope.informationClassAlert = {id: "id-123456"};
                $scope.closeAlert();

                expect($scope.informationClassAlert).toBe(null);
            });
        });

        describe('getFileList()', function() {
            it('fileListCollection is populated', function() {
                $scope.getFileList($scope.ip);
                expect($scope.fileListCollection.length).toBe(1);
            });
        });
    });
});
