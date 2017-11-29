angular.module('myApp').controller("ExportCtrl", function ($scope, appConfig, $http, TopAlert, $translate) {
    var vm = this;
    vm.$onInit = function() {
        $http.get(appConfig.djangoUrl + "submission-agreements/", { params: { pager: "none", published: true } })
            .then(function (response) {
                vm.sas = response.data;
                vm.sa = null;
            }).catch(function(response) {
                TopAlert.add(response.data.detail, "error");
            });

        $http.get(appConfig.djangoUrl+"profiles/", {params: { pager: "none"}})
            .then(function(response) {
                vm.profiles = response.data;
                vm.profile = null;
            }).catch(function(response) {
                TopAlert.add(response.data.detail, "error");
            });
    }

    $scope.encodeJson = function (obj) {
        return JSON.stringify(obj);
    };

    vm.profileFileName = function (item) {
        if (item) {
            var name = "profile_" + item.id + ".json";
            return name;
        }
    }
    vm.saFileName = function(item) {
        if(item) {
            var name = "submission_agreement_" + item.id + ".json";
            return name;
        }
    }
    vm.saLabel = function(sa) {
        var published = sa.published?" (Published)":"";
        return sa.name + published;
    }
    /**
     *
     * @param {Object} sa - Submission agreement to export
     * @param {Boolean} file - If true, export to file
     */
    vm.exportSa = function (sa, file) {

    }

    /**
     *
     * @param {Object} profile - Profile to export
     * @param {Boolean} file - If true, export to file
     */
    vm.exportProfile = function (profile, file) {

    }

});
