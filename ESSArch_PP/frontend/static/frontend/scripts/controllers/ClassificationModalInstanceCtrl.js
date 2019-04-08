angular
  .module('essarch.controllers')
  .controller('ClassificationModalInstanceCtrl', function(
    data,
    $http,
    appConfig,
    Notifications,
    $uibModalInstance,
    $translate,
    Structure
  ) {
    var $ctrl = this;
    $ctrl.name = null;
    $ctrl.newNode = {};
    $ctrl.options = {};
    $ctrl.nodeFields = [];
    $ctrl.structureFields = [];
    $ctrl.types = [];
    $ctrl.data = data;
    $ctrl.newStructure = {};
    $ctrl.$onInit = function() {
      if (data.node) {
        $ctrl.node = data.node;
      }
      if (data.structure) {
        $ctrl.structure = data.structure;
      }
      if(data.newStructure) {
        $http.get(appConfig.djangoUrl + 'structure-types/', {params: {pager: 'none'}}).then(function(response) {
          $ctrl.typeOptions = response.data;
          $ctrl.buildStructureForm();
        })
      } else {
        $http.get(appConfig.djangoUrl + 'structure-unit-types/', {params: {structure_type: data.structure.type.id, pager: 'none'}}).then(function(response) {
          if(data.children) {
            $ctrl.newNode.reference_code = (data.children.length + 1).toString();
          }
          $ctrl.structureUnitTypes = response.data;
          $ctrl.buildNodeForm();
        })
      }
    };

    $ctrl.buildStructureForm = function() {
      $ctrl.structureFields = [
        {
          key: 'name',
          type: 'input',
          templateOptions: {
            label: $translate.instant('NAME'),
            required: true
          },
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
              },
            },
            {
              className: 'col-xs-12 col-sm-6 px-0 pl-md-base',
              type: 'datepicker',
              key: 'end_date',
              templateOptions: {
                label: $translate.instant('ACCESS.VALID_DATE_END'),
                appendToBody: false,
              },
            },
          ],
        },
        {
          type: 'select',
          key: 'type',
          templateOptions: {
            options: $ctrl.typeOptions,
            valueProp: 'id',
            labelProp: 'name',
            label: $translate.instant('TYPE'),
            required: true
          },
        },
      ];
    }

    $ctrl.buildNodeForm = function() {
      $ctrl.nodeFields = [
        {
          templateOptions: {
            label: $translate.instant('ACCESS.REFERENCE_CODE'),
            type: 'text',
            required: true,
            focus: true,
          },
          type: 'input',
          key: 'reference_code',
        },
        {
          templateOptions: {
            type: 'text',
            label: $translate.instant('NAME'),
            required: true,
          },
          type: 'input',
          key: 'name',
        },
        {
          templateOptions: {
            label: $translate.instant('TYPE'),
            options: $ctrl.structureUnitTypes,
            valueProp: 'id',
            labelProp: 'name',
            required: true,
            notNull: true,
          },
          defaultValue: $ctrl.structureUnitTypes.length > 0 ? $ctrl.structureUnitTypes[0].id : null,
          type: 'select',
          key: 'type',
        },
        {
          templateOptions: {
            label: $translate.instant('DESCRIPTION'),
            type: 'text',
            rows: 3,
          },
          type: 'textarea',
          key: 'description',
        },
        {
          templateOptions: {
            type: 'text',
            label: $translate.instant('START_DATE'),
            appendToBody: false,
          },
          type: 'datepicker',
          key: 'start_date',
        },
        {
          templateOptions: {
            type: 'text',
            label: $translate.instant('END_DATE'),
            appendToBody: false,
          },
          type: 'datepicker',
          key: 'end_date',
        },
      ];
    };

    $ctrl.changed = function() {
      return !angular.equals($ctrl.newNode, {});
    };

    $ctrl.removeNode = function() {
      $http
        .delete(appConfig.djangoUrl + 'structures/' + data.structure.id + '/units/' + $ctrl.node.id)
        .then(function(response) {
          Notifications.add($translate.instant('ACCESS.NODE_REMOVED'), 'success');
          $uibModalInstance.close('added');
        });
    };

    $ctrl.submit = function() {
      if ($ctrl.form.$invalid) {
        $ctrl.form.$setSubmitted();
        return;
      }
      if ($ctrl.changed()) {
        $ctrl.submitting = true;
        $http
          .post(
            appConfig.djangoUrl + 'structures/' + data.structure.id + '/units/',
            angular.extend($ctrl.newNode, {
              parent: $ctrl.node.id,
            })
          )
          .then(function(response) {
            $ctrl.submitting = false;
            Notifications.add($translate.instant('ACCESS.NODE_ADDED'), 'success');
            $uibModalInstance.close(response.data);
          })
          .catch(function(response) {
            $ctrl.submitting = false;
          });
      }
    };
    /**
     * update new classification structure
     */
    $ctrl.update = function() {
      $http({
        method: 'PATCH',
        url: appConfig.djangoUrl + 'structures/' + data.structure.id + '/units/' + $ctrl.node.id + '/',
        data: {
          name: $ctrl.name,
        },
      }).then(function(response) {
        $uibModalInstance.close(response.data);
        Notifications.add($translate.instant('NODE_UPDATED'), 'success');
      });
    };
    /**
     * Save new classification structure
     */
    $ctrl.save = function() {
      if($ctrl.form.$invalid) {
        $ctrl.form.$setSubmitted();
        return;
      }
      Structure.new($ctrl.newStructure).$promise.then(function(response) {
        $uibModalInstance.close(response.data);
        Notifications.add($translate.instant('ACCESS.CLASSIFICATION_STRUCTURE_CREATED'), 'success');
      });
    };

    $ctrl.removing = false;
    $ctrl.remove = function(structure) {
      $ctrl.removing = true;
      Structure.remove({id: structure.id}).$promise.then(function(response) {
        $ctrl.removing = false;
        Notifications.add($translate.instant('ACCESS.CLASSIFICATION_STRUCTURE_REMOVED'), 'success');
        $uibModalInstance.close();
      });
    };
    $ctrl.cancel = function() {
      $uibModalInstance.dismiss('cancel');
    };
  });
