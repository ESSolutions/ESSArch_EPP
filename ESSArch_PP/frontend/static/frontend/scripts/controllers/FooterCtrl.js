angular.module('myApp').controller('FooterCtrl', function($scope, $rootScope, $timeout, $translate, $state) {
    var vm = this;
    var appName = " | ESSArch Preservation Platform";
    vm.pageTitle = "ESSArch Preservation Platform";
    vm.$onInit = function() {
        vm.currentYear = new Date().getFullYear();
    }
});