angular
  .module('essarch.controllers')
  .controller('StructureUnitRelationModalInstanceCtrl', function(
    $uibModalInstance,
    appConfig,
    data,
    $http,
    EditMode,
    $translate
  ) {
    var $ctrl = this;
    $ctrl.relation = {
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
        params: {search: search, page: 1, page_size: 10},
      }).then(function(response) {
        $ctrl.structure.options = response.data;
        return response.data;
      });
    };

    $ctrl.getStructureUnits = function(search, structure) {
      return $http({
        url: appConfig.djangoUrl + 'structure-units/',
        method: 'GET',
        params: {structure: structure, search: search, page: 1, page_size: 10},
      }).then(function(response) {
        if (angular.isUndefined(structure) || structure === null) {
          $ctrl.unit.options = [];
        } else {
          $ctrl.unit.options = response.data;
        }
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
        $ctrl.buildForm();
        EditMode.enable();
        return response.data;
      });
    };

    $ctrl.buildForm = function() {
      $ctrl.structureFields = [
        {
          type: 'uiselect',
          key: 'value',
          templateOptions: {
            required: true,
            options: function() {
              return $ctrl.structure.options;
            },
            valueProp: 'id',
            labelProp: 'name',
            placeholder: $translate.instant('ACCESS.CLASSIFICATION_STRUCTURE'),
            label: $translate.instant('ACCESS.CLASSIFICATION_STRUCTURE'),
            clearEnabled: true,
            appendToBody: false,
            refresh: function(search) {
              $ctrl.getStructures(search).then(function() {
                this.options = $ctrl.structure.options;
              });
            },
          },
        },
      ];
      $ctrl.unitFields = [];
      $ctrl.fields = [
        {
          type: 'uiselect',
          key: 'structure_unit',
          templateOptions: {
            required: true,
            options: function() {
              return $ctrl.unit.options;
            },
            valueProp: 'id',
            labelProp: 'name',
            required: true,
            placeholder: $translate.instant('ACCESS.STRUCTURE_UNIT'),
            label: $translate.instant('ACCESS.STRUCTURE_UNIT'),
            appendToBody: false,
            clearEnabled: true,
            refresh: function(search) {
              $ctrl.getStructureUnits(search, $ctrl.structure.value).then(function() {
                this.options = $ctrl.unit.options;
              });
            },
          },
        },
        {
          key: 'type',
          type: 'select',
          templateOptions: {
            options: $ctrl.options.type.choices,
            label: $translate.instant('TYPE'),
            labelProp: 'display_name',
            valueProp: 'value',
            notNull: true,
            required: true,
          },
          defaultValue: $ctrl.options.type.choices.length > 0 ? $ctrl.options.type.choices[0].value : null,
        },
        {
          className: 'row m-0',
          fieldGroup: [
            {
              className: 'col-xs-12 col-sm-6 px-0 pr-md-base',
              type: 'datepicker',
              key: 'start_date',
              templateOptions: {
                label: $translate.instant('ACCESS.VALID_DATE_START'),
                appendToBody: false,
                dateFormat: 'YYYY-MM-DD',
              },
            },
            {
              className: 'col-xs-12 col-sm-6 px-0 pl-md-base',
              type: 'datepicker',
              key: 'end_date',
              templateOptions: {
                label: $translate.instant('ACCESS.VALID_DATE_END'),
                appendToBody: false,
                dateFormat: 'YYYY-MM-DD',
              },
            },
          ],
        },
        {
          key: 'description',
          type: 'textarea',
          templateOptions: {
            label: $translate.instant('DESCRIPTION'),
            rows: 3,
          },
        },
      ];
    };

    $ctrl.add = function() {
      if ($ctrl.form.$invalid) {
        $ctrl.form.$setSubmitted();
        return;
      }
      $ctrl.adding = true;
      $http({
        url: appConfig.djangoUrl + 'structure-units/' + $ctrl.node.original.id + '/',
        method: 'PATCH',
        data: {
          structure: data.structure.id,
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
