angular.module('myApp').controller('ImportCtrl', function($q, $rootScope, $scope, $http, IP, Profile, SA, TopAlert) {
    var vm = this;
    vm.saProfile = {
        profiles: [],
        profile: null
    };

    vm.user = {
        username: null,
        password: null
    }

    vm.url = null;

    vm.getSaProfiles = function () {
        $scope.error = null;
        var auth = window.btoa(vm.user.username + ":" + vm.user.password);
        var headers = { "Authorization": "Basic " + auth };
        vm.url = vm.url.replace(/\/+$/, "");
        $http({
            method: "GET",
            url: vm.url + '/api/submission-agreements/',
            headers: headers,
            params: {
                published: true,
                pager: "none",
            },
            noAuth: true
        }).then(function (response) {
            vm.saProfile.profiles = response.data;
            vm.select = true;
        }).catch(function(response) {
            $scope.error = response.data.detail;
        })
    }

    vm.importSa = function (sa) {
        var auth = window.btoa(vm.user.username + ":" + vm.user.password);
        var headers = { "Authorization": "Basic " + auth };
        var promises = [];
        var profile_types = ["sip", "transfer_project", "submit_description", "preservation_metadata"];

        // Only include profiles matching the types listed in profile_types
        var pattern = new RegExp("^profile_(" + profile_types.join("|") + ")$");
        for (var key in sa) {
            if (pattern.test(key) && sa[key] != null) {
                promises.push($http.get(vm.url + '/api/profiles/' + sa[key] + '/', { headers: headers }).then(function (response) {
                    return Profile.new(response.data).$promise.then(function(response) {
                        return response;
                    }).catch(function(response) {
                        return response;
                    });
                }));
            }
        }
        $q.all(promises).then(function () {
            // Exclude profiles matching the types listed in profile_types
            var pattern = new RegExp("^profile_(?!(" + profile_types.join("|") + ")$)");
            for (var key in sa) {
                if (pattern.test(key)) {
                    delete sa[key];
                }
            }
            SA.new(sa).$promise.then(function (resource) {
                TopAlert.add("Submission agreement: \"" + resource.name + "\" has been imported" , "success", 5000);
                vm.select = false;
            }).catch(function(response) {
                TopAlert.add("Sa could not be added", "error", 5000);
            })
        })
    }

});
