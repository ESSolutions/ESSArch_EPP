+angular
  .module('essarch.controllers')
  .controller('AgentArchiveRelationModalInstanceCtrl', function(
    $uibModalInstance,
    appConfig,
    data,
    $http,
    EditMode,
    $scope
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

    $ctrl.add = function() {
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
    }

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
