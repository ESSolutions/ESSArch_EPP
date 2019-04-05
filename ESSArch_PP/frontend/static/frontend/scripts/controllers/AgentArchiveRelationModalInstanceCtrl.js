+angular
  .module('essarch.controllers')
  .controller('AgentArchiveRelationModalInstanceCtrl', function(
    $uibModalInstance,
    appConfig,
    data,
    $http,
    EditMode,
    $scope,
    $translate
  ) {
    var $ctrl = this;
    $ctrl.relationTemplate = {
      type: 1,
      description: '',
      start_date: null,
      end_date: null,
      archive: null,
    };
    $ctrl.options = {};
    $ctrl.data = data;
    $ctrl.fields = [];
    $ctrl.$onInit = function() {
      if (data.agent) {
        $ctrl.agent = angular.copy(data.agent);
      }
      if (data.relation) {
        $ctrl.relation = angular.copy(data.relation);
        $ctrl.relation.archive = data.relation.archive._id;
        $ctrl.relation.type = data.relation.type.id;
      } else {
        $ctrl.relation = $ctrl.relationTemplate;
      }
      return $http({
        url: appConfig.djangoUrl + 'agents/' + data.agent.id + '/archives/',
        method: 'OPTIONS',
      }).then(function(response) {
        $ctrl.options.type = response.data.actions.POST.type;
        $ctrl.loadForm();
        EditMode.enable();
        return response.data;
      });
    };

    $ctrl.getArchives = function(search) {
      return $http({
        url: appConfig.djangoUrl + 'tags/',
        mathod: 'GET',
        params: {page: 1, page_size: 10, index: 'archive', search: search},
      }).then(function(response) {
        $ctrl.options.archives = response.data.map(function(x) {
          return x.current_version;
        });
        return $ctrl.options.archives;
      });
    };
    $ctrl.loadForm = function() {
      $ctrl.fields = [
        {
          type: 'uiselect',
          key: 'archive',
          templateOptions: {
            required: true,
            options: function() {
              return $ctrl.options.archives;
            },
            valueProp: 'id',
            labelProp: 'name',
            placeholder: $translate.instant('ACCESS.ARCHIVE'),
            label: $translate.instant('ACCESS.ARCHIVE'),
            appendToBody: false,
            optionsFunction: function(search) {
              return $ctrl.options.archives;
            },
            refresh: function(search) {
              $ctrl.getArchives(search).then(function() {
                this.options = $ctrl.options.archives;
              });
            },
          },
        },
        {
          type: 'select',
          key: 'type',
          templateOptions: {
            label: $translate.instant('TYPE'),
            options: $ctrl.options.type.choices,
            required: true,
            labelProp: 'display_name',
            valueProp: 'value',
            defaultValue: $ctrl.options.type.choices[0].value,
            notNull: true,
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
          }
        }
      ];
    };

    $ctrl.add = function() {
      if ($ctrl.form.$invalid) {
        $ctrl.form.$setSubmitted();
        return
      }
      $ctrl.adding = true;
      $http({
        url: appConfig.djangoUrl + 'agents/' + $ctrl.agent.id + '/archives/',
        method: 'POST',
        data: $ctrl.relation,
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

    $ctrl.save = function() {
      if ($ctrl.form.$invalid) {
        $ctrl.form.$setSubmitted();
        return
      }
      $ctrl.saving = true;
      $http({
        url: appConfig.djangoUrl + 'agents/' + $ctrl.agent.id + '/archives/' + $ctrl.relation.id + '/',
        method: 'PATCH',
        data: $ctrl.relation,
      })
        .then(function(response) {
          $ctrl.saving = false;
          EditMode.disable();
          $uibModalInstance.close(response.data);
        })
        .catch(function() {
          $ctrl.saving = false;
          EditMode.disable();
        });
    };

    $ctrl.remove = function() {
      $ctrl.removing = true;
      $http({
        url: appConfig.djangoUrl + 'agents/' + $ctrl.agent.id + '/archives/' + $ctrl.relation.id + '/',
        method: 'DELETE',
      })
        .then(function(response) {
          $ctrl.removing = false;
          EditMode.disable();
          $uibModalInstance.close(response.data);
        })
        .catch(function() {
          $ctrl.removing = false;
          EditMode.disable();
        });
    };

    $ctrl.cancel = function() {
      EditMode.disable();
      $uibModalInstance.dismiss('cancel');
    };
    $scope.$on('modal.closing', function(event, reason, closed) {
      if (
        (data.allow_close === null || angular.isUndefined(data.allow_close) || data.allow_close !== true) &&
        (reason === 'cancel' || reason === 'backdrop click' || reason === 'escape key press')
      ) {
        var message = $translate.instant('UNSAVED_DATA_WARNING');
        if (!confirm(message)) {
          event.preventDefault();
        } else {
          EditMode.disable();
        }
      }
    });
  });