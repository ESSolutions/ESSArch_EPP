angular
  .module('essarch.controllers')
  .controller('AgentNoteModalInstanceCtrl', function(
    $uibModalInstance,
    $scope,
    $translate,
    $http,
    appConfig,
    data,
    EditMode
  ) {
    var $ctrl = this;
    $ctrl.note;
    $ctrl.noteTemplate = {
      create_date: null,
      href: '',
      revise_date: null,
      text: null,
      type: null,
    };
    $ctrl.fields = [];
    $ctrl.resetNote = function() {
      $ctrl.note = angular.copy($ctrl.noteTemplate);
    };

    $ctrl.$onInit = function() {
      return $http({
        url: appConfig.djangoUrl + 'agents/',
        method: 'OPTIONS',
      }).then(function(response) {
        $ctrl.typeOptions = response.data.actions.POST.notes.child.children.type.choices;
        EditMode.enable();
        if (data.note) {
          data.note.type = data.note.type.id;
          $ctrl.note = angular.copy(data.note);
        } else {
          $ctrl.resetNote();
        }
        $ctrl.loadForm();
      });
    };

    $ctrl.loadForm = function() {
      $ctrl.fields = [
        {
          type: 'select',
          key: 'type',
          templateOptions: {
            label: $translate.instant('TYPE'),
            options: $ctrl.typeOptions,
            required: true,
            labelProp: 'display_name',
            valueProp: 'value',
            defaultValue: $ctrl.typeOptions[0].value,
            notNull: true,
          },
        },
        {
          key: 'text',
          type: 'textarea',
          templateOptions: {
            label: $translate.instant('ACCESS.TEXT'),
            rows: 3,
            required: true,
          },
        },
        {
          key: 'href',
          type: 'input',
          templateOptions: {
            label: $translate.instant('ACCESS.HREF'),
          },
        },
        {
          type: 'datepicker',
          key: 'create_date',
          templateOptions: {
            label: $translate.instant('CREATE_DATE'),
            appendToBody: false,
            required: true,
          },
        },
        {
          type: 'datepicker',
          key: 'revise_date',
          templateOptions: {
            label: $translate.instant('ACCESS.REVISE_DATE'),
            appendToBody: false,
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
      var notes = angular.copy(data.agent.notes);
      notes.forEach(function(x) {
        if (typeof x.type === 'object') {
          x.type = x.type.id;
        }
      });
      $http({
        url: appConfig.djangoUrl + 'agents/' + data.agent.id + '/',
        method: 'PATCH',
        data: {notes: [$ctrl.note].concat(notes)},
      })
        .then(function(response) {
          $ctrl.adding = false;
          EditMode.disable();
          $uibModalInstance.close(response.data);
        })
        .catch(function(response) {
          $ctrl.adding = false;
        });
    };

    $ctrl.save = function() {
      if ($ctrl.form.$invalid) {
        $ctrl.form.$setSubmitted();
        return;
      }
      $ctrl.saving = true;
      var notes = angular.copy(data.agent.notes);
      notes.forEach(function(x, idx, array) {
        if (typeof x.type === 'object') {
          x.type = x.type.id;
        }
        if (x.id === $ctrl.note.id) {
          array[idx] = $ctrl.note;
        }
      });
      $http({
        url: appConfig.djangoUrl + 'agents/' + data.agent.id + '/',
        method: 'PATCH',
        data: {notes: notes},
      })
        .then(function(response) {
          $ctrl.saving = false;
          EditMode.disable();
          $uibModalInstance.close(response.data);
        })
        .catch(function(response) {
          $ctrl.saving = false;
        });
    };

    $ctrl.remove = function() {
      $ctrl.removing = true;
      var notes = angular.copy(data.agent.notes);
      notes.forEach(function(x, idx, array) {
        if (typeof x.type === 'object') {
          x.type = x.type.id;
        }
        if (x.id === $ctrl.note.id) {
          array.splice(idx, 1);
        }
      });
      $http({
        url: appConfig.djangoUrl + 'agents/' + data.agent.id + '/',
        method: 'PATCH',
        data: {notes: notes},
      })
        .then(function(response) {
          $ctrl.removing = false;
          EditMode.disable();
          $uibModalInstance.close(response.data);
        })
        .catch(function(response) {
          $ctrl.removing = false;
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
