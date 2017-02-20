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

angular.module('myApp').controller('DropdownCtrl', function ($scope, $log, $rootScope, $state, $stateParams, djangoAuth, $window, $translate, $uibModal) {
    $scope.items = [
        'Shortcut 1',
        'Shortcut 2',
        'Shortcut 3'
    ];
    var options, optionsAuth;
    $translate(['LOGIN', 'CHANGEPASSWORD', 'LOGOUT']).then(function(translations) {
        $scope.logIn = translations.LOGIN;
        $scope.changePassword = translations.CHANGEPASSWORD;
        $scope.logOut = translations.LOGOUT;
        options = [
            {
                label: $scope.logIn,
                link: 'login',
                click: function(){$scope.gotoLink('login');}
            }
        ];
        optionsAuth = [
            {
                label: $scope.changePassword,
                link: '',
                click: function(){$scope.changePasswordModal();}
            },
            {
                label: $scope.logOut,
                link: 'logout',
                click: function(){$scope.gotoLink('logout');}
            }
        ];
    });
    $scope.$watch(function() {
        return djangoAuth.authenticated;
    }, function() {
        if(!djangoAuth.authenticated){
            $scope.editUserOptions = options;
        } else {
            $scope.editUserOptions = optionsAuth;
        }
    }, true);
    $scope.name = "";
    $scope.gotoLink = function(link) {
        if(link != 'logout') {
            $window.location.href = link;
        } else {
            $state.go(link);
        }
    };
    $scope.status = {
        isopen: false
    };

    $scope.toggled = function(open) {
        $log.log('Dropdown is now: ', open);
    };

    $scope.toggleDropdown = function($event) {
        $event.preventDefault();
        $event.stopPropagation();
        $scope.status.isopen = !$scope.status.isopen;
    };
    $scope.changePasswordModal = function () {
        var modalInstance = $uibModal.open({
            animation: true,
            ariaLabelledBy: 'modal-title',
            ariaDescribedBy: 'modal-body',
            templateUrl: 'static/frontend/views/change_password_modal.html',
            scope: $scope,
            size: 'md',
            controller: 'ModalInstanceCtrl',
            controllerAs: '$ctrl'
        })
        modalInstance.result.then(function (data) {
        }, function () {
            $log.info('modal-component dismissed at: ' + new Date());
        });
    }

    $scope.appendToEl = angular.element(document.querySelector('#dropdown-long-content'));
});
