angular
  .module('essarch.controllers')
  .controller('StructureUnitRelationModalInstanceCtrl', function($uibModalInstance, appConfig, data, $http, EditMode) {
    var $ctrl = this;
    $ctrl.relation = {
      type: 1,
      description: '',
      start_date: null,
      end_date: null,
      create_date: new Date(),
      revise_date: null,
      structure_unit: null,
    };
    $ctrl.structure = {
      value: null,
      options: [],
    };
    $ctrl.unit = {
      value: null,
      options: [],
    };
    $ctrl.options = {};
    $ctrl.getStructures = function(search) {
      return $http({
        url: appConfig.djangoUrl + 'structures/',
        method: 'GET',
        params: {search: search, page: 1, page_size: 10}
      }).then(function(response) {
        $ctrl.structure.options = response.data;
        return response.data;
      });
    };

    $ctrl.getStructureUnits = function(structure, search) {
      return $http({
        url: appConfig.djangoUrl + 'structure-units/',
        method: 'GET',
        params: {structure: structure, search: search, page: 1, page_size: 10},
      }).then(function(response) {
        $ctrl.unit.options = response.data;
        return response.data;
      });
    };

    $ctrl.$onInit = function() {
      if (data.node) {
        $ctrl.node = angular.copy(data.node);
      }
      return $http({
        url: appConfig.djangoUrl + 'structure-units/',
        method: 'OPTIONS',
      }).then(function(response) {
        $ctrl.options.type = response.data.actions.POST.related_structure_units.child.children.type;
        EditMode.enable();
        return response.data;
      });
    };

    $ctrl.add = function() {
      $ctrl.adding = true;
      $http({
        url: appConfig.djangoUrl + 'structure-units/' + $ctrl.node.original.id + '/',
        method: 'PATCH',
        data: {
          related_structure_units: angular.copy($ctrl.node).original.related_structure_units.concat([$ctrl.relation]),
        },
      })
        .then(function(response) {
          $ctrl.adding = false;
          EditMode.disable();
          $uibModalInstance.close(response.data);
        })
        .catch(function() {
          $ctrl.adding = false;
          EditMode.disable();
        });
    };
    $ctrl.cancel = function() {
      EditMode.disable();
      $uibModalInstance.dismiss('cancel');
    };
  });
