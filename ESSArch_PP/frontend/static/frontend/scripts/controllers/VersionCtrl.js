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

angular.module('essarch.controllers').controller('VersionCtrl', function($scope, myService, $window, $state, marked, $anchorScroll, $location, $translate) {
    myService.getVersionInfo().then(function(result) {
        $scope.sysInfo = result;
    });
    $scope.redirectToEss = function(){
        $window.open('http://www.essolutions.se', '_blank');
    };
    $scope.scrollToLink = function(link) {
        $location.hash(link);
        $anchorScroll();
    }

    $scope.gotoDocs = function() {
        $window.open("/docs/"+$translate.use()+"/user_guide/index.html", '_blank');
    }

    $scope.docs = $translate.instant('DOCS');
    $scope.sysInfo = $translate.instant('SYSTEMINFORMATION');
    $scope.support = $translate.instant('SUPPORT');
    $scope.tabs = [
        {
            label: $scope.docs,
            templateUrl: 'static/frontend/views/docs.html'
        },
        {
            label: $scope.sysInfo,
            templateUrl: "static/frontend/views/sysinfo.html"
        },
        {
            label: $scope.support,
            templateUrl: "static/frontend/views/support.html"
        }
    ];
});
