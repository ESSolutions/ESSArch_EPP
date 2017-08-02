angular.module('myApp').controller('SaEditorCtrl', function(SA, Profile, $scope, $rootScope, $http, appConfig) {
    var vm = this;
    $scope.edit = false;
    vm.saProfile = null;
    vm.saProfiles = [];
    vm.$onInit = function() {
        SA.query().$promise.then(function(resource) {
            vm.saProfiles = resource;
        });
    }
    vm.newSa = function() {
        vm.getProfiles();
        vm.saProfile = {};
        $scope.edit = true;
    }
    vm.chooseSa = function(sa) {
        vm.getProfiles();
        vm.createProfileModel(sa);
        vm.saProfile = sa;
        vm.saModel = sa;
        $scope.edit = true;
    }
    vm.createProfileModel = function(sa) {
        for(var key in sa) {
            if(/^profile/.test(key) && sa[key] != null) {
                vm.profileModel[key] = sa[key];
            }
        }
        console.log(vm.profileModel)
    }
    vm.getProfiles = function() {
        Profile.query().$promise.then(function(resource) {
            resource.forEach(function(profile) {
                vm.profiles[profile.profile_type].push(profile);
            });
        });
    }
    vm.profiles = {
        transfer_project: [],
        content_type: [],
        data_selection: [],
        authority_information: [],
        archival_description: [],
        import: [],
        submit_description: [],
        sip: [],
        aip: [],
        dip: [],
        workflow: [],
        preservation_metadata: [],
    };
    vm.saModel = {};
    vm.saFields = [
    {
        "templateOptions": {
            "label": "name",
        },
        "type": "input",
        "key": "name",
    },
    {
        "templateOptions": {
            "label": "type",
        },
        "type": "input",
        "key": "type",
    },
    {
        "templateOptions": {
            "label": "status",
        },
        "type": "input",
        "key": "status",
    },
    {
        "templateOptions": {
            "label": "label",
        },
        "type": "input",
        "key": "label",
    },
    {
        "templateOptions": {
            "label": "cm_version",
        },
        "type": "input",
        "key": "cm_version",
    },
    {
        "templateOptions": {
            "label": "cm_release_date",
        },
        "type": "input",
        "key": "cm_release_date",
    },
    {
        "templateOptions": {
            "label": "cm_change_authority",
        },
        "type": "input",
        "key": "cm_change_authority",
    },
    {
        "templateOptions": {
            "label": "cm_change_description",
        },
        "type": "input",
        "key": "cm_change_description",
    },
    {
        "templateOptions": {
            "label": "cm_sections_affected",
        },
        "type": "input",
        "key": "cm_sections_affected",
    },
    {
        "templateOptions": {
            "label": "producer_organization",
        },
        "type": "input",
        "key": "producer_organization",
    },
    {
        "templateOptions": {
            "label": "producer_main_name",
        },
        "type": "input",
        "key": "producer_main_name",
    },
    {
        "templateOptions": {
            "label": "producer_main_address",
        },
        "type": "input",
        "key": "producer_main_address",
    },
    {
        "templateOptions": {
            "label": "producer_main_phone",
        },
        "type": "input",
        "key": "producer_main_phone",
    },
    {
        "templateOptions": {
            "label": "producer_main_email",
        },
        "type": "input",
        "key": "producer_main_email",
    },
    {
        "templateOptions": {
            "label": "producer_main_additional",
        },
        "type": "input",
        "key": "producer_main_additional",
    },
    {
        "templateOptions": {
            "label": "producer_individual_name",
        },
        "type": "input",
        "key": "producer_individual_name",
    },
    {
        "templateOptions": {
            "label": "producer_individual_role",
        },
        "type": "input",
        "key": "producer_individual_role",
    },
    {
        "templateOptions": {
            "label": "producer_individual_phone",
        },
        "type": "input",
        "key": "producer_individual_phone",
    },
    {
        "templateOptions": {
            "label": "producer_individual_email",
        },
        "type": "input",
        "key": "producer_individual_email",
    },
    {
        "templateOptions": {
            "label": "producer_individual_additional",
        },
        "type": "input",
        "key": "producer_individual_additional",
    },
    {
        "templateOptions": {
            "label": "archivist_organization",
        },
        "type": "input",
        "key": "archivist_organization",
    },
    {
        "templateOptions": {
            "label": "archivist_main_name",
        },
        "type": "input",
        "key": "archivist_main_name",
    },
    {
        "templateOptions": {
            "label": "archivist_main_address",
        },
        "type": "input",
        "key": "archivist_main_address",
    },
    {
        "templateOptions": {
            "label": "archivist_main_phone",
        },
        "type": "input",
        "key": "archivist_main_phone",
    },
    {
        "templateOptions": {
            "label": "archivist_main_email",
        },
        "type": "input",
        "key": "archivist_main_email",
    },
    {
        "templateOptions": {
            "label": "archivist_main_additional",
        },
        "type": "input",
        "key": "archivist_main_additional",
    },
    {
        "templateOptions": {
            "label": "archivist_individual_name",
        },
        "type": "input",
        "key": "archivist_individual_name",
    },
    {
        "templateOptions": {
            "label": "archivist_individual_role",
        },
        "type": "input",
        "key": "archivist_individual_role",
    },
    {
        "templateOptions": {
            "label": "archivist_individual_phone",
        },
        "type": "input",
        "key": "archivist_individual_phone",
    },
    {
        "templateOptions": {
            "label": "archivist_individual_email",
        },
        "type": "input",
        "key": "archivist_individual_email",
    },
    {
        "templateOptions": {
            "label": "archivist_individual_additional",
        },
        "type": "input",
        "key": "archivist_individual_additional",
    },
    {
        "templateOptions": {
            "label": "designated_community_description",
        },
        "type": "input",
        "key": "designated_community_description",
    },
    {
        "templateOptions": {
            "label": "designated_community_individual_name",
        },
        "type": "input",
        "key": "designated_community_individual_name",
    },
    {
        "templateOptions": {
            "label": "designated_community_individual_role",
        },
        "type": "input",
        "key": "designated_community_individual_role",
    },
    {
        "templateOptions": {
            "label": "designated_community_individual_phone",
        },
        "type": "input",
        "key": "designated_community_individual_phone",
    },
    {
        "templateOptions": {
            "label": "designated_community_individual_email",
        },
        "type": "input",
        "key": "designated_community_individual_email",
    },
    {
        "templateOptions": {
            "label": "designated_community_individual_additional",
        },
        "type": "input",
        "key": "designated_community_individual_additional",
    }
    ];
    vm.profileModel = {};
    vm.profileFields = [
    {
        "templateOptions": {
            "label": "profile_transfer_project",
            "options": vm.profiles["transfer_project"],
        },
        "type": "select",
        "key": "profile_transfer_project",
    },
    {
        "templateOptions": {
            "label": "profile_content_type",
            "options": vm.profiles["content_type"],
        },
        "type": "select",
        "key": "profile_content_type",
    },
    {
        "templateOptions": {
            "label": "profile_data_selection",
            "options": vm.profiles["data_selection"],
        },
        "type": "select",
        "key": "profile_data_selection",
    },
    {
        "templateOptions": {
            "label": "profile_authority_information",
            "options": vm.profiles["authority_information"],
        },
        "type": "select",
        "key": "profile_authority_information",
    },
    {
        "templateOptions": {
            "label": "profile_archival_description",
            "options": vm.profiles["archival_description"],
        },
        "type": "select",
        "key": "profile_archival_description",
    },
    {
        "templateOptions": {
            "label": "profile_import",
            "options": vm.profiles["import"],
        },
        "type": "select",
        "key": "profile_import",
    },
    {
        "templateOptions": {
            "label": "profile_submit_description",
            "options": vm.profiles["submit_description"],
        },
        "type": "select",
        "key": "profile_submit_description",
    },
    {
        "templateOptions": {
            "label": "profile_sip",
            "options": vm.profiles["sip"],
        },
        "type": "select",
        "key": "profile_sip",
    },
    {
        "templateOptions": {
            "label": "profile_aip",
            "options": vm.profiles["aip"],
        },
        "type": "select",
        "key": "profile_aip",
    },
    {
        "templateOptions": {
            "label": "profile_dip",
            "options": vm.profiles["dip"],
        },
        "type": "select",
        "key": "profile_dip",
    },
    {
        "templateOptions": {
            "label": "profile_workflow",
            "options": vm.profiles["workflow"],
        },
        "type": "select",
        "key": "profile_workflow",
    },
    {
        "templateOptions": {
            "label": "profile_preservation_metadata",
            "options": vm.profiles["preservation_metadata"],
        },
        "type": "select",
        "key": "profile_preservation_metadata",
    },
    ]
});