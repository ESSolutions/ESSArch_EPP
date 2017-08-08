angular.module('myApp').controller('AddCtrl', function (ProfileMakerTemplate, $http, $scope, appConfig) {
  console.log("add controller")
  var vm = this;
  vm.model = {};
  vm.options = {};

  vm.onSubmit = function() {
    if (vm.model) {
      // send the image data
      ProfileMakerTemplate.add(vm.model).$promise.then(function (response) {
        vm.model = {};
      });
    }
    //   vm.options.updateInitialValue();
  }

  vm.fields = [
    {
      key: 'name',
      type: 'input',
      templateOptions: {
        type: 'text',
        label: 'Name',
        placeholder: '',
        required: true
      }
    },
    {
      key: 'prefix',
      type: 'input',
      templateOptions: {
        type: 'text',
        label: 'prefix',
        placeholder: '',
        required: true
      }
    },
    {
      key: 'root_element',
      type: 'input',
      templateOptions: {
        type: 'text',
        label: 'Root Element',
        placeholder: '',
        required: true
      }
    },
    {
      key: 'schemaURL',
      type: 'input',
      templateOptions: {
        type: "url",
        label: 'Schema URL'
      }
    },
  ];
  vm.originalFields = angular.copy(vm.fields);
  $scope.formData = null;
  // recieve data from element
  var unlisten = $scope.$on('fileToUpload', function (event, arg) {
    $scope.formData = arg;
  });

});