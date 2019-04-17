angular
  .module('essarch.controllers')
  .controller('AddNodeModalInstanceCtrl', function(
    Search,
    $translate,
    $uibModalInstance,
    appConfig,
    $http,
    data,
    $scope,
    Notifications,
    $rootScope
  ) {
    var $ctrl = this;
    $ctrl.node = data.node.original;
    $ctrl.nodeFields = [];
    $ctrl.newNode = {
      reference_code: (data.node.children.length + 1).toString(),
      index: 'component',
    };
    $ctrl.options = {};
    $ctrl.nodeFields = [];
    $ctrl.types = [];

    $ctrl.$onInit = function() {
      $http
        .get(appConfig.djangoUrl + 'tag-version-types/', {params: {archive_type: false, pager: 'none'}})
        .then(function(response) {
          $ctrl.typeOptions = response.data;
          $ctrl.loadForm();
        });
    };

    $ctrl.loadForm = function() {
      $ctrl.nodeFields = [
        {
          templateOptions: {
            type: 'text',
            label: $translate.instant('NAME'),
            required: true,
            focus: true,
          },
          type: 'input',
          key: 'name',
        },
        {
          templateOptions: {
            label: $translate.instant('TYPE'),
            required: true,
            options: $ctrl.typeOptions,
            valueProp: 'pk',
            labelProp: 'name',
          },
          defaultValue: $ctrl.typeOptions.length > 0 ? $ctrl.typeOptions[0].pk : null,
          type: 'select',
          key: 'type',
        },
        {
          templateOptions: {
            label: $translate.instant('ACCESS.REFERENCE_CODE'),
            type: 'text',
            required: true,
          },
          type: 'input',
          key: 'reference_code',
        },
        {
          key: 'description',
          type: 'textarea',
          templateOptions: {
            label: $translate.instant('DESCRIPTION'),
            rows: 3,
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
                label: $translate.instant('START_DATE'),
                appendToBody: false,
              },
            },
            {
              className: 'col-xs-12 col-sm-6 px-0 pl-md-base',
              type: 'datepicker',
              key: 'end_date',
              templateOptions: {
                label: $translate.instant('END_DATE'),
                appendToBody: false,
              },
            },
          ],
        },
      ];
    };

    $ctrl.changed = function() {
      return !angular.equals($ctrl.newNode, {});
    };

    $ctrl.submit = function() {
      if ($ctrl.form.$invalid) {
        $ctrl.form.$setSubmitted();
        return;
      }
      if ($ctrl.changed()) {
        $ctrl.submitting = true;
        var params = angular.extend($ctrl.newNode, {archive: data.archive, structure: data.structure});
        if ($ctrl.node._is_structure_unit) params.structure_unit = $ctrl.node._id;
        else {
          params.parent = $ctrl.node._id;
        }

      $rootScope.skipErrorNotification = true;
      Search.addNode(params)
          .then(function(response) {
            $ctrl.submitting = false;
            Notifications.add($translate.instant('ACCESS.NODE_ADDED'), 'success');
            $uibModalInstance.close(response.data);
          })
          .catch(function(response) {
            $ctrl.nonFieldErrors = response.date.non_field_errors;
            $ctrl.submitting = false;
          });
      }
    };
    $ctrl.cancel = function() {
      $uibModalInstance.dismiss('cancel');
    };
  });
