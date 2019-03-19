angular.module('essarch.controllers').controller('SearchFilterCtrl', function($scope, $window, $rootScope) {
  var vm = this;
  var onclickSet = false;
  vm.q = '';
  vm.$onInit = function() {
    if (angular.isUndefined(vm.ngModel)) {
      vm.selected = [];
    } else {
      vm.selected = vm.ngModel;
    }
    vm.update({
      search: vm.q,
    });
    if (vm.ngChange) {
      vm.ngChange();
    }
  };

  $scope.$watch(
    function() {
      return vm.ngModel;
    },
    function(oldval, newval) {
      if (vm.ngChange) {
        vm.ngChange();
      }
    }
  );

  $rootScope.$on('CLOSE_FILTERS', function(e, data) {
    if(data.except !== $scope.$id) {
      vm.resultListVisible = false;
      onclickSet = false;
    }
  })

  vm.search = function() {
    vm.update({
      search: vm.q,
    });
  };
  vm.updateModel = function() {
    if (vm.selected.length <= 0) {
      vm.ngModel = null;
    } else {
      vm.ngModel = vm.selected;
    }
  };

  vm.select = function(item) {
    vm.selected.push(item);
    vm.updateModel();
  };

  vm.deselect = function(item) {
    vm.selected.forEach(function(x, idx, array) {
      if (x[vm.valueProp] === item[vm.valueProp]) {
        array.splice(idx, 1);
      }
    });
    vm.updateModel();
  };
  vm.notSelected = function(item) {
    var notSelected = true;
    vm.selected.forEach(function(x) {
      if (x[vm.valueProp] === item[vm.valueProp]) {
        notSelected = false;
      }
    });
    return notSelected;
  };

  vm.optionsEmpty = function() {
    var list = angular.copy(vm.options);
    var toDelete = [];
    list.forEach(function(x, idx, array) {
      if (!vm.notSelected(x)) {
        toDelete.push(idx);
      }
    });
    for (var i = toDelete.length; i > 0; i--) {
      list.splice(toDelete[i], 1);
    }
    return list.length <= 0;
  };
  vm.openOptions = function(evt) {
    vm.resultListVisible = true;
    if($window.onclick && !onclickSet) {
      $rootScope.$broadcast('CLOSE_FILTERS', {except: $scope.$id});
    }
    onclickSet = true;
    $window.onclick = function(event) {
      var clickedElement = $(event.target);
      if (!clickedElement) return;
      var elementClasses = event.target.classList;
      var clickedOnFilter =
        elementClasses.contains('filter-'+$scope.$id) ||
        elementClasses.contains('filter-options-item') ||
        clickedElement.parents('filter-options').length;

      if (!clickedOnFilter) {
        vm.resultListVisible = false;
        $window.onclick = null;
        onclickSet = false;
        $scope.$apply();
      }
    };
  };
});
