angular.module('myApp').controller('QueuesCtrl', function(appConfig, $scope, $rootScope, Storage, $interval) {
    var vm = this;
    $scope.select = true;
    vm.ioQueue = [];
    vm.robotQueue = [];
    var ioInterval;
    $interval.cancel(ioInterval);
    ioInterval = $interval(function() {
        vm.getIoQueue();
    }, appConfig.queueInterval);

    var robotInterval;
    $interval.cancel(robotInterval);
    robotInterval = $interval(function() {
        vm.getRobotQueue();
    }, appConfig.queueInterval);

    $rootScope.$on('$stateChangeStart', function() {
		$interval.cancel(ioInterval);
		$interval.cancel(robotInterval);
	});

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