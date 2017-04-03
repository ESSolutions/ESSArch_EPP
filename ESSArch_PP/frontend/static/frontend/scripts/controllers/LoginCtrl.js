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

angular.module('myApp').controller('LoginCtrl', function ($scope, $location, myService, $state, $stateParams, $rootScope, djangoAuth, Validate, $http, PermRoleStore, PermPermissionStore){
    $scope.redirectAdmin = function () {
        $window.location.href="/admin/";
    }
    $scope.model = {'username':'','password':''};
    $scope.complete = false;
    $scope.login = function(formData){
        $scope.errors = [];
        Validate.form_validation(formData,$scope.errors);
        if(!formData.$invalid){
            djangoAuth.login($scope.model.username, $scope.model.password)
                .then(function(data){
                    // success case
                    djangoAuth.profile().then(function(response){
                        $rootScope.auth = response.data;
                        $rootScope.listViewColumns = myService.generateColumns(response.data.ip_list_columns).activeColumns;
                        PermPermissionStore.clearStore();
                        PermRoleStore.clearStore();
                        myService.getPermissions(response.data.permissions);
                    });
                    $state.go('home.myPage');
                },function(data){
                    // error case
                    $scope.errors = data;
                    console.log($scope.errors);
                });
        }
    }
});

