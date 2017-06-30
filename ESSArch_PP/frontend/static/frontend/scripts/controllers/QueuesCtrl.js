angular.module('myApp').controller('QueuesCtrl', function($scope, $rootScope, Storage) {
    var vm = this;
    console.log("Queues page opened");
    $scope.text = "hello this is queues page";
    $scope.select = true;
    vm.ioQueue = [];
    vm.robotQueue = [];

    vm.getIoQueue = function() {
        Storage.getIoQueue().then(function(result) {
            vm.ioQueue = result;
        });
    }

    vm.getRobotQueue = function() {
        Storage.getRobotQueue().then(function(result) {
            vm.robotQueue = result;
        })
    }

    vm.getIoQueue();
    vm.getRobotQueue();
});