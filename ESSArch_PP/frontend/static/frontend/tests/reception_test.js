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

    var $controller, $scope;

    beforeEach(inject(function(_$controller_){
        $controller = _$controller_;
    }));

    describe('toggling', function() {
        var $scope, controller;

        beforeEach(inject(function($rootScope){
            $scope = $rootScope.$new();
            controller = $controller('ReceptionCtrl', { $scope: $scope });
        }));

        describe('$scope.select', function() {
            it('when true sets false', function() {
                $scope.select = true;
                $scope.toggleSelectView();

                expect($scope.select).toBe(false);
            });

            it('when false sets true', function() {
                $scope.select = false;
                $scope.toggleSelectView();

                expect($scope.select).toBe(true);
            });
        });

        describe('$scope.subSelect', function() {
            it('when true sets false', function() {
                $scope.subSelect = true;
                $scope.toggleSubSelectView();

                expect($scope.subSelect).toBe(false);
            });

            it('when false sets true', function() {
                $scope.subSelect = false;
                $scope.toggleSubSelectView();

                expect($scope.subSelect).toBe(true);
            });
        });

        describe('$scope.toggleEditView', function() {
            it('when true sets false', function() {
                $scope.edit = true;
                $scope.toggleEditView();

                expect($scope.edit).toBe(false);
                expect($scope.eventlog).toBe(false);
            });

            it('when false sets true', function() {
                $scope.edit = false;
                $scope.toggleEditView();

                expect($scope.edit).toBe(true);
                expect($scope.eventlog).toBe(true);
            });
        });

        describe('$scope.toggleEventLogView', function() {
            it('when true sets false', function() {
                $scope.eventlog = true;
                $scope.toggleEventlogView();

                expect($scope.eventlog).toBe(false);
            });

            it('when false sets true', function() {
                $scope.eventlog = false;
                $scope.toggleEventlogView();

                expect($scope.eventlog).toBe(true);
            });
        });
    });
});
