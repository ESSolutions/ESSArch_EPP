/*
ESSArch is an open source archiving and digital preservation system

ESSArch Preservation Platform (EPP)
Copyright (C) 2005-2017 ES Solutions AB

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.

Contact information:
Web - http://www.essolutions.se
Email - essarch@essolutions.se
*/

angular.module('myApp').factory('listViewService', function($q, $http, $state, $log, appConfig, $rootScope, $filter, linkHeaderParser) {
    //Go to Given state
    function changePath(state) {
        $state.go(state);
    }
    //Gets data for list view i.e information packages
    function getListViewData(pageNumber, pageSize, filters, sortString, searchString, state, viewType, columnFilters, archived) {
        if(archived != true) {
            archived = false;
        }
        var ipUrl = appConfig.djangoUrl + 'information-packages/';
        if ($rootScope.ipUrl) {
            ipUrl = $rootScope.ipUrl;
        }
        var promise = $http({
            method: 'GET',
            url: ipUrl,
            params: angular.extend({
                page: pageNumber,
                page_size: pageSize,
                ordering: sortString,
                state: state,
                search: searchString,
                view_type: viewType,
                archived: archived
            }, columnFilters)
        }).then(function successCallback(response) {
            count = response.headers('Count');
            if (count == null) {
                count = response.data.length;
            }
            return {
                count: count,
                data: response.data
            };
        });
        return promise;
    }

    //Fetches IP's for given workarea (ingest or access)
    function getWorkareaData(workarea, pageNumber, pageSize, filters, sortString, searchString, viewType, columnFilters) {
        var ipUrl = appConfig.djangoUrl + 'workarea/';
        var promise = $http({
            method: 'GET',
            url: ipUrl,
            params: angular.extend({
                type: workarea,
                page: pageNumber,
                page_size: pageSize,
                ordering: sortString,
                search: searchString,
                view_type: viewType
            }, columnFilters)
        }).then(function successCallback(response) {
            count = response.headers('Count');
            if (count == null) {
                count = response.data.length;
            }
            return {
                count: count,
                data: response.data
            };
        });
        return promise;
    }

        //Fetches IP's for given workarea (ingest or access)
    function getDipPage(pageNumber, pageSize, filters, sortString, searchString, columnFilters) {
        var ipUrl = appConfig.djangoUrl + 'information-packages/';
        var promise = $http({
            method: 'GET',
            url: ipUrl,
            params: angular.extend({
                package_type: 4,
                page: pageNumber,
                page_size: pageSize,
                ordering: sortString,
                search: searchString,
            }, columnFilters)
        }).then(function successCallback(response) {
            count = response.headers('Count');
            if (count == null) {
                count = response.data.length;
            }
            return {
                count: count,
                data: response.data
            };
        });
        return promise;
    }
    function getOrderPage(pageNumber, pageSize, filters, sortString, searchString) {
        var orderUrl = appConfig.djangoUrl + 'orders/';
        var promise = $http({
            method: 'GET',
            url: orderUrl,
            params: {
                page: pageNumber,
                page_size: pageSize,
                ordering: sortString,
                search: searchString,
            }
        }).then(function successCallback(response) {
            count = response.headers('Count');
            if (count == null) {
                count = response.data.length;
            }
            return {
                count: count,
                data: response.data
            };
        });
        return promise;
    }

    function getReceptionIps(pageNumber, pageSize, filters, sortString, searchString, state, columnFilters) {
        var promise = $http({
                method: 'GET',
                url: appConfig.djangoUrl + 'ip-reception/',
                params: angular.extend({
                    page: pageNumber,
                    page_size: pageSize,
                    ordering: sortString,
                    state: state,
                    search: searchString
                }, columnFilters)
            })
            .then(function successCallback(response) {
                count = response.headers('Count');
                if (count == null) {
                    count = response.data.length;
                }
                return {
                    count: count,
                    data: response.data
                };
            }, function errorCallback(response) {});
        return promise;
    }

    function getStorageMediums(pageNumber, pageSize, filters, sortString, searchString) {
        return $http({
            method: 'GET',
            url: appConfig.djangoUrl + "storage-mediums/",
            params: {
                page: pageNumber,
                page_size: pageSize,
                ordering: sortString,
                search: searchString
            }
        }).then(function successCallback(response) {
            count = response.headers('Count');
            if (count == null) {
                count = response.data.length;
            }
            return {
                count: count,
                data: response.data
            };
        });
    }

    function getStorageObjects(pageNumber, pageSize, medium, sortString, searchString) {
        return $http({
            method: 'GET',
            url: medium.url + "storage-objects/",
            params: {
                page: pageNumber,
                page_size: pageSize,
                ordering: sortString,
                search: searchString
            }
        }).then(function successCallback(response) {
            count = response.headers('Count');
            if (count == null) {
                count = response.data.length;
            }
            return {
                count: count,
                data: response.data
            };
        });
    }
    //Get data for status view. child steps and tasks
    function getStatusViewData(ip, expandedNodes) {
        var promise = $http({
            method: 'GET',
            url: ip.url + 'steps/'
        }).then(function(response) {
            var steps = response.data;
            steps.forEach(function(step) {
                step.time_started = $filter('date')(step.time_created, "yyyy-MM-dd HH:mm:ss");
                step.children = [{ val: -1 }];
                step.childrenFetched = false;
            });
            return setExpanded(steps, expandedNodes);
        });
        return promise;
    }
    //Prepare the data for tree view in status view
    function getTreeData(row, expandedNodes) {
        return getStatusViewData(row, expandedNodes);
    }

    function preserveIp(ip, request) {
        return $http({
            method: 'POST',
            url: ip.url + 'preserve/',
            data: request
        }).then(function(response) {
            return response;
        });
    }
    //Add a new event
    function addEvent(ip, eventType, eventDetail, outcome) {
        var promise = $http({
            method: 'POST',
            url: appConfig.djangoUrl + "events/",
            data: {
                "eventType": eventType.id,
                "eventOutcomeDetailNote": eventDetail,
                "eventOutcome": outcome.value,
                "information_package": ip.id
            }

        }).then(function(response) {
            return response.data;
        }, function() {

        });
        return promise;
    }
    //Returns all events for one ip
    function getEvents(ip, pageNumber, pageSize, sortString) {
        var promise = $http({
                method: 'GET',
                url: ip.url + 'events/',
                params: { page: pageNumber, page_size: pageSize, ordering: sortString }
            })
            .then(function successCallback(response) {
                count = response.headers('Count');
                if (count == null) {
                    count = response.data.length;
                }
                return {
                    count: count,
                    data: response.data
                };
            }, function errorCallback(response) {});
        return promise;
    }
    //Gets event type for dropdown selection
    function getEventlogData() {
        var promise = $http({
                method: 'GET',
                url: appConfig.djangoUrl + 'event-types/'
            })
            .then(function successCallback(response) {
                return response.data;
            }, function errorCallback(response) {});
        return promise;

    }
    //Returns map structure for a profile
    function getStructure(profileUrl) {
        return $http({
            method: 'GET',
            url: profileUrl
        }).then(function(response) {
            return response.data.structure;
        }, function(response) {});
    }
    //returns all SA-profiles and current as an object
    function getSaProfiles(ip) {
        var sas = [];
        var saProfile = {
            entity: "PROFILE_SUBMISSION_AGREEMENT",
            profile: null,
            profiles: [

            ],
        };
        var promise = $http({
                method: 'GET',
                url: appConfig.djangoUrl + 'submission-agreements/'
            })
            .then(function successCallback(response) {
                sas = response.data;
                saProfile.profiles = [];
                saProfile.profileObjects = sas;
                sas.forEach(function(sa) {
                    saProfile.profiles.push(sa);
                    if (ip.submission_agreement == sa.url) {
                        saProfile.profile = sa;
                        saProfile.locked = ip.submission_agreement_locked;
                    }
                });
                return saProfile;
            }, function errorCallback(response) {});
        return promise;
    }

    function getProfileByTypeFromSA(sa, type) {
        return sa['profile_' + type];
    }

    function getProfileByTypeFromIP(ip, type) {
        return ip['profile_' + type];
    }

    function findProfileByUrl(url, profiles) {
        var p = null;

        profiles.forEach(function(profile) {
            if (profile.url == url) {
                p = profile;
            }
        });

        return p;
    }

    //Ligher fetching of profiles start
    function createProfileObjMinified(type, profiles, ip, sa) {
        var required = false;
        var locked = false;
        var checked = false;
        var profile = null;

        p = getProfileByTypeFromIP(ip, type);
        if (p) {
            profile_from_ip = p;
            profile = profile_from_ip;
            locked = p.LockedBy ? true : false;
            checked = p.included
        }
        p = getProfileByTypeFromSA(sa, type);
        if (p) {
            checked = true;
            required = true;
            if (profile == null) {
                profile = p;
            }
        }
        active = profile;
        if (profile) {
            profiles = [profile];
        }
        return {
            type_label: getProfileTypeLabel(type),
            profile_type: type,
            active: active,
            checked: checked,
            required: required,
            profiles: profiles,
            locked: locked
        };
    }

    function getProfilesFromIp(sa, ip) {
        var selectCollapse = [];
        if (sa == null) {
            return [];
        }
        if (sa.id != null) {
            if (ip.profile_transfer_project) {
                selectCollapse.push(createProfileObjMinified("transfer_project", [ip.profile_transfer_project], ip, sa));
            } else {
                selectCollapse.push(createProfileObjMinified("transfer_project", [], ip, sa));
            }
            if (ip.profile_submit_description) {
                selectCollapse.push(createProfileObjMinified("submit_description", [ip.profile_submit_description], ip, sa));
            } else {
                selectCollapse.push(createProfileObjMinified("submit_description", [], ip, sa));
            }
            if (ip.profile_sip) {
                selectCollapse.push(createProfileObjMinified("sip", [ip.profile_sip], ip, sa));
            } else {
                selectCollapse.push(createProfileObjMinified("sip", [], ip, sa));
            }
            /*
            if(ip.profile_aip) {
                selectCollapse.push(createProfileObjMinified("aip", [ip.profile_aip], ip, sa));
            } else {
                selectCollapse.push(createProfileObjMinified("aip", [], ip, sa));
            }
            if(ip.profile_dip) {
                selectCollapse.push(createProfileObjMinified("dip", [ip.profile_dip], ip, sa));
            } else {
                selectCollapse.push(createProfileObjMinified("dip", [], ip, sa));
            }
            if(ip.profile_content_type) {
                selectCollapse.push(createProfileObjMinified("content_type", [ip.profile_content_type], ip, sa));
            } else {
                selectCollapse.push(createProfileObjMinified("content_type", [], ip, sa));
            }
            if(ip.profile_authority_information) {
                selectCollapse.push(createProfileObjMinified("authority_information", [ip.profile_authority_information], ip, sa));
            } else {
                selectCollapse.push(createProfileObjMinified("authority_information", [], ip, sa));
            }
            if(ip.profile_archival_description) {
                selectCollapse.push(createProfileObjMinified("archival_description", [ip.profile_archival_description], ip, sa));
            } else {
                selectCollapse.push(createProfileObjMinified("archival_description", [], ip, sa));
            }
            if(ip.profile_preservation_metadata) {
                selectCollapse.push(createProfileObjMinified("preservation_metadata", [ip.profile_preservation_metadata], ip, sa));
            } else {
                selectCollapse.push(createProfileObjMinified("preservation_metadata", [], ip, sa));
            }
            if(ip.profile_data_selection) {
                selectCollapse.push(createProfileObjMinified("data_selection", [ip.profile_data_selection], ip, sa));
            } else {
                selectCollapse.push(createProfileObjMinified("data_selection", [], ip, sa));
            }
            if(ip.profile_import) {
                selectCollapse.push(createProfileObjMinified("import", [ip.profile_import], ip, sa));
            } else {
                selectCollapse.push(createProfileObjMinified("import", [], ip, sa));
            }
            if(ip.profile_workflow) {
                selectCollapse.push(createProfileObjMinified("workflow", [ip.profile_workflow], ip, sa));
            } else {
                selectCollapse.push(createProfileObjMinified("workflow", [], ip, sa));
            }*/
            return selectCollapse;
        }
    }
    //Lighter fetching of profiles end
    function getProfileTypeLabel(type) {
        var typeMap = {
            "transfer_project": "Transfer project",
            "submit_description": "Submit description",
            "sip": "SIP",
            "aip": "AIP",
            "dip": "DIP",
            "content_type": "Content type",
            "authority_information": "Authority information",
            "archival_description": "Archival description",
            "preservation_metadata": "Preservation metadata",
            "data_selection": "Data selection",
            "import": "Import",
            "workflow": "Workflow"
        };
        return typeMap[type];
    }

    //Execute prepare ip, which creates a new IP
    function prepareIp(label) {
        return $http({
            method: 'POST',
            url: appConfig.djangoUrl + "information-packages/",
            data: { label: label }
        }).then(function(response) {
            return "created";
        });

    }
    //Returns IP
    function getIp(url) {
        return $http({
            method: 'GET',
            url: url
        }).then(function(response) {
            return response.data;
        }, function(response) {});
    }
    //Returns SA
    function getSa(url) {
        return $http({
            method: 'GET',
            url: url
        }).then(function(response) {
            return response.data;
        }, function(response) {});
    }
    //Get list of files in Ip
    function getFileList(ip) {
        return getIp(ip.url).then(function(result) {
            var array = [];
            var tempElement = {
                filename: result.object_path,
                created: result.create_date,
                size: result.object_size
            };
            array.push(tempElement);
            return array;
        });
    }

    function prepareDip(label, objectIdentifierValue, orders) {
        return $http.post(appConfig.djangoUrl + "information-packages/prepare-dip/",
            {
                label: label,
                object_identifier_value: objectIdentifierValue,
                orders: orders
            }).then(function (response) {
                return response.data;
            });
    };

    function createDip(ip) {
        return $http.post(ip.url + 'create-dip/').then(function(response) {
            return response.data;
        });
    }

    function prepareOrder(label) {
        return $http( {
            method: 'POST',
            url: appConfig.djangoUrl + 'orders/',
            data: {label: label}
        }).then(function(response){
            return response.data;
        })
    }
    function getWorkareaDir(workareaType, pathStr) {
        var sendData;
        if (pathStr == "") {
            sendData = {
                type: workareaType
            };
        } else {
            sendData = {
                path: pathStr,
                type: workareaType
            };
        }
        var url = appConfig.djangoUrl + "workarea-files/";
        return $http.get(url, {params: sendData})
            .then(function(response) {
                return response.data;
            });
    }

    function getDipDir(ip, pathStr) {
        if (pathStr == "") {
            sendData = {};
        } else {
            sendData = {
                path: pathStr,
            };
        }
        var url = ip.url + "files/";
        return $http.get(url, {params: sendData})
            .then(function(response) {
                return response.data;
            });
    }

    function addFileToDip(ip, path, file, destination, type) {
        var src = path + file.name;
        var dst = destination + file.name;
        return $http.post(appConfig.djangoUrl + "workarea-files/add-to-dip/", {
            dip: ip.id,
            src: src,
            dst: dst,
            type: type
        }).then(function(response){
            return response;
        });
    }
    function addNewFolder(ip, path, file) {
        return $http.post(ip.url + "files/",
        {
            path: path + file.name, 
            type: file.type
        }).then(function(response) {
            return response;
        });
    }
    function deleteFile(ip, path, file) {
        return $http({
            method: "DELETE",
            url: ip.url + "files/",
            data: { path: path + file.name },
            headers: {
                'Content-type': 'application/json;charset=utf-8'
            }
        })
        .then(function(response) {
            return response;
        });
    }

    /*******************/
    /*HELPER FUNCTIONS*/
    /*****************/

    //Set expanded nodes in array of steps
    function setExpanded(steps, expandedNodes) {
        expandedNodes.forEach(function(node) {
            steps.forEach(function(step) {
                if (step.id == node.id) {
                    step.expanded = true;
                    getChildrenForStep(step, node.page_number).then(function() {
                        if (step.children != null) {
                            if (step.children.length > 0) {
                                setExpanded(step.children, expandedNodes);
                            }
                        }
                    });
                }
            });
        });
        return steps;
    }

    function getChildrenForStep(step, page_number) {
        page_size = 10;
        if (angular.isUndefined(page_number) || !page_number) {
            step.page_number = 1;
        } else {
            step.page_number = page_number;
        }
        return $http({
            method: 'GET',
            url: step.url + "children/",
            params: {
                page: step.page_number,
                page_size: page_size
            }
        }).then(function(response) {
            var link = linkHeaderParser.parse(response.headers('Link'));
            var count = response.headers('Count');
            if (count == null) {
                count = response.data.length;
            }
            step.pages = Math.ceil(count / page_size);
            link.next ? step.next = link.next : step.next = null;
            link.prev ? step.prev = link.prev : step.prev = null;
            step.page_number = page_number || 1;
            var placeholder_removed = false;
            if (response.data.length > 0) {
                // Delete placeholder
                step.children.pop();
                placeholder_removed = true;
            }
            var tempChildArray = [];
            response.data.forEach(function(child) {
                child.label = child.name;
                child.user = child.responsible;
                if (child.flow_type == "step") {
                    child.isCollapsed = false;
                    child.tasksCollapsed = true;
                    child.children = [{ val: -1 }];
                    child.childrenFetched = false;
                }
                tempChildArray.push(child);
            });
            step.children = tempChildArray;


            step.children = step.children.map(function(c) {
                c.time_started = $filter('date')(c.time_started, "yyyy-MM-dd HH:mm:ss");
                return c
            });
        });
    }

    //Gets all profiles of a specific profile type for an IP
    function getProfiles(type) {
        var promise = $http({
                method: 'GET',
                url: appConfig.djangoUrl + "profiles/",
                params: { type: type }
            })
            .then(function successCallback(response) {
                return response.data;
            }, function errorCallback(response) {
                console.log(response.status);
            });
        return promise;
    };

    function getProfilesMin(type) {
        var promise = $http({
                method: 'GET',
                url: appConfig.djangoUrl + "profiles/",
                params: { type: type }
            })
            .then(function successCallback(response) {
                response.data.forEach(function(profileObj) {
                    profileObj.profile_name = profileObj.name;
                });
                return response.data;
            }, function errorCallback(response) {
                console.log(response.status);
            });
        return promise;
    };

    //Checks if a given sa is locked to a given ip
    function saLocked(sa, ip) {
        locked = false;
        ip.locks.forEach(function(lock) {
            if (lock.submission_agreement == sa.url) {
                locked = true;
            }
        });
        return locked;
    }

    //Checks if a profile is locked
    function profileLocked(profileObject, sa, locks) {
        profileObject.locked = false;
        locks.forEach(function(lock) {
            if (lock.submission_agreement == sa && lock.profile == profileObject.profile.url) {
                profileObject.locked = true;
            }
        });
        return profileObject;
    }
    //Return child steps list and corresponding tasks on all levels of child steps
    function getChildSteps(childSteps) {
        var stepsToRemove = [];
        childSteps.forEach(function(child, idx) {
            child.child_steps = getChildSteps(child.child_steps);
            var preserved_tasks = [];
            child.tasks.forEach(function(task) {
                if (!task.hidden) {
                    task.user = task.responsible;
                    task.time_created = task.time_started;
                    task.isTask = true;
                    preserved_tasks.push(task);
                }
            });
            child.tasks = preserved_tasks;

            child.children = child.child_steps.concat(child.tasks);
            if (child.children.length == 0) {
                stepsToRemove.push(idx);
            }
            child.isCollapsed = false;
            child.tasksCollapsed = true;

            child.children.sort(function(a, b) {
                if (a.time_created != null && b.time_created == null) return -1;
                if (a.time_created == null && b.time_created != null) return 1;
                var a = new Date(a.time_created),
                    b = new Date(b.time_created);
                if (a < b) return -1;
                if (a > b) return 1;
                return 0;
            });

            child.children = child.children.map(function(c) {
                c.time_created = $filter('date')(c.time_created, "yyyy-MM-dd HH:mm:ss");
                return c
            });
        });
        stepsToRemove.forEach(function(idx) {
            childSteps.splice(idx, 1);
        });
        return childSteps;
    }
    return {
        getChildrenForStep: getChildrenForStep,
        getListViewData: getListViewData,
        getReceptionIps: getReceptionIps,
        getStorageMediums: getStorageMediums,
        getStorageObjects: getStorageObjects,
        addEvent: addEvent,
        getEvents: getEvents,
        getTreeData: getTreeData,
        getStatusViewData: getStatusViewData,
        changePath: changePath,
        getEventlogData: getEventlogData,
        getSaProfiles: getSaProfiles,
        prepareIp: prepareIp,
        getIp: getIp,
        getSa: getSa,
        getFileList: getFileList,
        getStructure: getStructure,
        getProfilesFromIp: getProfilesFromIp,
        getProfiles: getProfiles,
        getProfilesMin: getProfilesMin,
        getWorkareaDir: getWorkareaDir,
        getDipDir: getDipDir,
        preserveIp: preserveIp,
        getWorkareaData: getWorkareaData,
        addFileToDip: addFileToDip,
        addNewFolder: addNewFolder,
        deleteFile: deleteFile,
        prepareDip: prepareDip,
        getDipPage: getDipPage,
        getOrderPage: getOrderPage,
        prepareOrder: prepareOrder,
        createDip: createDip,
    };
});