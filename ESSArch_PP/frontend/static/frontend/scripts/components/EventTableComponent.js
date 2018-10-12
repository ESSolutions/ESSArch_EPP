angular.module('essarch.components').component('eventTable', {
    templateUrl: 'static/frontend/views/event_table.html',
    controller: 'EventCtrl',
    controllerAs: 'vm',
    bindings: {
        ip: "<"
    }
  });
