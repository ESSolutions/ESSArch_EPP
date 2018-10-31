angular.module('essarch.controllers').controller('ArchiveManagerCtrl', function($scope, $http, appConfig, Search, Notifications, $translate) {
    var vm = this;
    vm.structure = null;
    vm.structures = [];
    vm.$onInit = function() {
        $http({
            method: 'GET',
            url: appConfig.djangoUrl + 'classification-structures/',
        }).then(function(response) {
            vm.structures = response.data;
            if(vm.structures.length > 0) {
                vm.structure = vm.structures[0];
            }
        }).catch(function(response) {
            if(![401, 403, 500, 503].includes(response.status)) {
                if(response.data && response.data.detail) {
                    Notifications.add(response.data.detail, "error");
                } else {
                    Notifications.add($translate('UNKNOWN_ERROR'), 'error')
                }
            }
        })
    }
    vm.createArchive = function (archiveName, structureName, type, referenceCode, archiveCreator, archiveResponsible) {
        Search.addNode(
            {
                name: archiveName,
                structure: structureName,
                index: 'archive',
                type: type,
                reference_code: referenceCode,
                archive_creator: archiveCreator,
                archive_responsible: archiveResponsible
            }
        ).then(function (response) {
            vm.archiveName = null;
            vm.structure = null;
            vm.nodeType = null;
            vm.referenceCode = null;
            vm.archiveResponsible = null;
            vm.archiveCreator = null;
            Notifications.add($translate.instant('NEW_ARCHIVE_CREATED'), 'success');
        }).catch(function(response) {
            if(![401, 403, 500, 503].includes(response.status)) {
                if(response.data && response.data.detail) {
                    Notifications.add(response.data.detail, "error");
                } else {
                    Notifications.add($translate('UNKNOWN_ERROR'), 'error')
                }
            }
        })
    }
})
