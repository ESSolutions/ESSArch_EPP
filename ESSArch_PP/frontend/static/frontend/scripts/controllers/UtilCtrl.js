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

angular.module('myApp').controller('UtilCtrl', function(TopAlert, $scope, $state, $location, $window, $rootScope, $timeout, $http, appConfig, myService, permissionConfig) {
    $scope.$state = $state;
    $scope.reloadPage = function (){
        $state.reload();
    }
    $scope.redirectAdmin = function () {
        $window.location.href="/admin/";
    }
    $scope.infoPage = function() {
        $state.go('home.myPage');
    }
    $scope.checkPermissions = function(permissions) {
        return myService.checkPermissions(permissions);
    }

    $scope.getPermissions = function(page) {
        return nestedPermissions(Object.resolve(page, permissionConfig));
    }
    $scope.showAlert = function() {
        TopAlert.show();
    }
});
