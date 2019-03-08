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
      href: null,
      revise_date: null,
      text: null,
      type: null,
    };
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
      });
    };

    $ctrl.add = function() {
      $ctrl.adding = true;
      var notes = angular.copy(data.agent.notes);
      notes.forEach(function(x) {
        x.type = x.type.id;
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

    $ctrl.cancel = function() {
      EditMode.disable();
      $uibModalInstance.dismiss('cancel');
    };

    $scope.$on('modal.closing', function(event, reason, closed) {
      if (reason === 'cancel' || reason === 'backdrop click' || reason === 'escape key press') {
        var message = $translate.instant('UNSAVED_DATA_WARNING');
        if (!confirm(message)) {
          event.preventDefault();
        } else {
          EditMode.disable();
        }
      }
    });
  });
