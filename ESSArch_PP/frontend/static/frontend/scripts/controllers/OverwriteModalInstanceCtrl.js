angular.module('essarch.controllers').controller('OverwriteModalInstanceCtrl', function ($uibModalInstance, djangoAuth, data, Profile, SA, Notifications) {
    var $ctrl = this;
    if(data.file) {
        $ctrl.file = data.file;
    }
    if(data.type) {
        $ctrl.type = data.type;
    }
    if(data.profile) {
        $ctrl.profile = data.profile;
    }
    $ctrl.overwriteProfile = function() {
        return Profile.update($ctrl.profile).$promise.then(function(resource) {
            Notifications.add("Profile: \"" + resource.name + "\" has been imported. <br/>ID: " + resource.id , "success", 5000, {isHtml: true});
            $ctrl.data = {
                status: "overwritten"
            }
            $uibModalInstance.close($ctrl.data);
            return resource;
        }).catch(function(repsonse) {
            Notifications.add(response.detail, "error");
        })
    }
    $ctrl.overwriteSa = function() {
        return SA.update($ctrl.profile).$promise.then(function(resource) {
            Notifications.add("Submission agreement: \"" + resource.name + "\" has been imported. <br/>ID: " + resource.id , "success", 5000, {isHtml: true});
            $ctrl.data = {
                status: "overwritten"
            }
            $uibModalInstance.close($ctrl.data);
            return resource;
        }).catch(function(response) {
            Notifications.add("Submission Agreement " + $ctrl.profile.name + " is Published and can not be overwritten", "error");
        })
    }
    $ctrl.overwrite = function () {
        $ctrl.data = {
            status: "overwritten"
        }
        $uibModalInstance.close($ctrl.data);
    };
    $ctrl.cancel = function () {
        $uibModalInstance.dismiss('cancel');
    };
});
