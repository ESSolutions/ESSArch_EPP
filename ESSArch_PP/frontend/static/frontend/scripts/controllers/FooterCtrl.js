angular.module('essarch.controllers').controller('FooterCtrl', function($scope, $rootScope, $timeout, $translate, $state) {
    var vm = this;
    vm.pageTitle = "ESSArch Preservation Platform";
    vm.$onInit = function() {
        vm.currentYear = new Date().getFullYear();
    }
});
