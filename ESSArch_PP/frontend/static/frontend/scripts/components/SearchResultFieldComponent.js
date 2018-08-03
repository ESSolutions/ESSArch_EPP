angular.module('myApp').component('resultField', {
    templateUrl: 'static/frontend/views/search_result_field.html',
    controller: 'SearchResultFieldCtrl',
    controllerAs: 'vm',
    bindings: {
        label: "@",
        data: "<",
        type: "@",
        break: "<"
    }
  });
