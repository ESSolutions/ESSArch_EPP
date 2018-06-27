angular.module('myApp').controller('ArchiveManagerCtrl', function($scope, $http, appConfig, Search, Notifications) {
    var vm = this;
    vm.structure = null;
    vm.structures = [];
    vm.$onInit = function() {
        $http({
            method: 'GET',
            url: appConfig.djangoUrl + 'classification-structures/',
        }).then(function(response) {
            vm.structures = response.data;
        }).catch(function(response) {
            if(response.data && response.data.detail) {
                Notifications.add(response.data.detail, 'error');
            } else {
                Notifications.add('Unknown error!' + response, 'error');
            }
        })
    }
    vm.createArchive = function(archiveName, structureName, type, referenceCode) {
        Search.addNode({name: archiveName, structure: structureName, index: 'archive', type: type, reference_code: referenceCode}).then(function(response) {
            vm.archiveName = null;
            vm.structure = null;
            vm.nodeType = null;
            vm.referenceCode = null;
            Notifications.add($translate.instant('NEW_ARCHIVE_CREATED'), 'success');
        }).catch(function(response) {
            Notifications.add(response.data.detail, 'error');
        })
    }
})
