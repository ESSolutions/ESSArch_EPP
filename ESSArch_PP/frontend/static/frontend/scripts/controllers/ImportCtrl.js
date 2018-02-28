angular.module('myApp').controller('ImportCtrl', function($q, $rootScope, $scope, $http, IP, Profile, SA, TopAlert, $uibModal) {
    var vm = this;
    $scope.angular = angular;
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
                    var data = response.data;
                    return Profile.new(data).$promise.then(function(response) {
                        return response;
                    }).catch(function(response) {
                        if(response.status == 409) {
                            profileExistsModal(data);
                        } else if(response.status == 400) {
                            TopAlert.add("Invalid profile", "error");
                        } else if(response.status >= 500) {
                            TopAlert.add("Server error", "error");
                        }
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
                TopAlert.add("Submission agreement: \"" + resource.name + "\" has been imported. ID: " + resource.id , "success", 5000);
                vm.select = false;
            }).catch(function(response) {
                if(response.status == 409) {
                    saProfileExistsModal(sa);
                } else if(response.status == 400) {
                    TopAlert.add("Invalid submission agreement", "error");
                } else if(response.status >= 500) {
                    TopAlert.add("Server error", "error");
                }
            })
        })
    }

    vm.addSaFromFile = function(sa){
        if(angular.isUndefined(sa)) {
            sa = vm.saFromFile;
        }
        var parsedSa;
        try {
            parsedSa = JSON.parse(sa);
        } catch(e) {
            TopAlert.add(e, "error");
            return;
        }
        SA.new(parsedSa).$promise.then(function (resource) {
            TopAlert.add("Submission agreement: \"" + resource.name + "\" has been imported. ID: " + resource.id , "success", 5000);
            vm.select = false;
        }).catch(function(response) {
            if(response.status == 409) {
                saProfileExistsModal(parsedSa);
            } else if(response.status == 400) {
                TopAlert.add("Invalid submission agreement", "error");
            } else if(response.status >= 500) {
                TopAlert.add("Server error", "error");
            }
        });
    }
    vm.addProfileFromFile = function(profile) {
        var parsedProfile;
        try {
            parsedProfile = JSON.parse(profile);
        } catch(e) {
            TopAlert.add(e, "error");
            return;
        }
        Profile.new(parsedProfile).$promise.then(function(resource) {
            TopAlert.add("Profile: \"" + resource.name + "\" has been imported. ID: " + resource.id , "success", 5000);
            return resource;
        }).catch(function(response) {
            if(response.status == 409) {
                profileExistsModal(parsedProfile);
            } else if(response.status == 400) {
                TopAlert.add("Invalid profile", "error");
            } else if(response.status >= 500) {
                TopAlert.add("Server error", "error");
            }
            return response;
        });
    }

    $scope.$watch(function(){return vm.saFromFile}, function() {
        if(vm.saFromFile) {
            vm.addSaFromFile(vm.saFromFile);
        }
    });

    $scope.$watch(function(){return vm.profileFromFile}, function() {
        if(vm.profileFromFile){
            vm.addProfileFromFile(vm.profileFromFile);
        }
    });

    function saProfileExistsModal(profile) {
        var modalInstance = $uibModal.open({
            animation: true,
            ariaLabelledBy: 'modal-title',
            ariaDescribedBy: 'modal-body',
            templateUrl: 'static/frontend/views/sa-exists-modal.html',
            controller: 'OverwriteModalInstanceCtrl',
            controllerAs: '$ctrl',
            resolve: {
                data: function () {
                    return {
                        profile: profile,
                    };
                }
            },
        })
        modalInstance.result.then(function (data) {
        });
    }
    function profileExistsModal(profile) {
        var modalInstance = $uibModal.open({
            animation: true,
            ariaLabelledBy: 'modal-title',
            ariaDescribedBy: 'modal-body',
            templateUrl: 'static/frontend/views/profile-exists-modal.html',
            controller: 'OverwriteModalInstanceCtrl',
            controllerAs: '$ctrl',
            resolve: {
                data: function () {
                    return {
                        profile: profile,
                    };
                }
            },
        })
        modalInstance.result.then(function (data) {
        });
    }
    vm.triggerProfileUpload = function() {
        document.getElementById('profile-upload').click();
    }
    vm.triggerSaUpload = function() {
        document.getElementById('sa-upload').click();
    }
});
