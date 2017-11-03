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

angular.module('myApp').factory('listViewService', function(Tag, Profile, IP, Workarea, WorkareaFiles, Order, IPReception, Event, EventType, SA, Step, $q, $http, $state, $log, appConfig, $rootScope, $filter, linkHeaderParser) {
    //Go to Given state
    function changePath(state) {
        $state.go(state);
    }
    //Gets data for list view i.e information packages
    function getListViewData(pageNumber, pageSize, filters, sortString, searchString, state, viewType, columnFilters, archived, workarea) {
        var data = angular.extend({
            page: pageNumber,
            page_size: pageSize,
            ordering: sortString,
            state: state,
            search: searchString,
            view_type: viewType,
            archived: archived,
        }, columnFilters);

        if (workarea) {
            data = angular.extend(data, {workarea: workarea});
        }

        if ($rootScope.selectedTag != null) {

            return Tag.information_packages(angular.extend({id: $rootScope.selectedTag.id }, data)).$promise.then(function (resource) {
                var count = resource.$httpHeaders('Count');
                if (count == null) {
                    count = resource.length;
                }
                return {
                    count: count,
                    data: resource
                };
            })
        } else {

            return IP.query(data).$promise.then(function (resource) {
                var count = resource.$httpHeaders('Count');

                if (count == null) {
                    count = resource.length;
                }
                return {
                    count: count,
                    data: resource
                };
            })
        }
    }

    //Fetches IP's for given workarea (ingest or access)
    function getWorkareaData(workarea, pageNumber, pageSize, filters, sortString, searchString, viewType, columnFilters) {
        return Workarea.query(
            angular.extend({
                type: workarea,
                page: pageNumber,
                page_size: pageSize,
                ordering: sortString,
                search: searchString,
                view_type: viewType,
                tag: $rootScope.selectedTag != null ? $rootScope.selectedTag.id : null,
            }, columnFilters)
        ).$promise.then(function (resource) {
            count = resource.$httpHeaders('Count');
            if (count == null) {
                count = resource.length;
            }
            return {
                count: count,
                data: resource
            };
        });
    }

    //Fetches IP's for given workarea (ingest or access)
    function getDipPage(pageNumber, pageSize, filters, sortString, searchString, columnFilters) {
        return IP.query(
             angular.extend({
                package_type: 4,
                page: pageNumber,
                page_size: pageSize,
                ordering: sortString,
                search: searchString,
                tag: $rootScope.selectedTag != null ? $rootScope.selectedTag.id : null,
            }, columnFilters)
        ).$promise.then(function (resource) {
            count = resource.$httpHeaders('Count');
            if (count == null) {
                count = resource.length;
            }
            return {
                count: count,
                data: resource
            };
        });
        return promise;
    }
    function getOrderPage(pageNumber, pageSize, filters, sortString, searchString) {
        return Order.query({
            page: pageNumber,
            page_size: pageSize,
            ordering: sortString,
            search: searchString,
            tag: $rootScope.selectedTag != null ? $rootScope.selectedTag.id : null,
        }).$promise.then(function (resource) {
            count = resource.$httpHeaders('Count');
            if (count == null) {
                count = resource.length;
            }
            return {
                count: count,
                data: resource
            };
        });
    }

    function getReceptionIps(pageNumber, pageSize, filters, sortString, searchString, state, columnFilters) {
        return IPReception.query(
                angular.extend({
                    page: pageNumber,
                    page_size: pageSize,
                    ordering: sortString,
                    state: state,
                    search: searchString,
                    tag: $rootScope.selectedTag != null ? $rootScope.selectedTag.id : null,
                }, columnFilters)
            ).$promise.then(function (resource) {
                count = resource.$httpHeaders('Count');
                if (count == null) {
                    count = resource.length;
                }
                return {
                    count: count,
                    data: resource
                };
            });
    }

    //Get data for status view. child steps and tasks
    function getStatusViewData(ip, expandedNodes) {
        return IP.steps({ id: ip.id }).$promise.then(function (data) {
            var steps = data;
            steps.forEach(function (step) {
                step.time_started = $filter('date')(step.time_created, "yyyy-MM-dd HH:mm:ss");
                step.children = [{ val: -1 }];
                step.childrenFetched = false;
            });
            return expandAndGetChildren(steps, expandedNodes);
        })
    }
    //Prepare the data for tree view in status view
    function getTreeData(row, expandedNodes) {
        return getStatusViewData(row, expandedNodes);
    }

    //Add a new event
    function addEvent(ip, eventType, eventDetail, outcome) {
        return Event.save({
            "eventType": eventType.eventType,
            "eventOutcomeDetailNote": eventDetail,
            "eventOutcome": outcome.value,
            "information_package": ip.id
        }).$promise.then(function (response) {
            return response;
        });
    }
    //Returns all events for one ip
    function getEvents(ip, pageNumber, pageSize, sortString, columnFilters, searchString) {
        return IP.events(angular.extend({
            id: ip.id,
            page: pageNumber,
            page_size: pageSize,
            search: searchString,
            ordering: sortString
        }, columnFilters)).$promise.then(function (resource) {
                count = resource.$httpHeaders('Count');
                if (count == null) {
                    count = resource.length;
                }
                return {
                    count: count,
                    data: resource
                };
            });
    }
    //Gets event type for dropdown selection
    function getEventlogData() {
        return EventType.query().$promise.then(function (data) {
            return data;
        });
    }
    //Returns map structure for a profile
    function getStructure(profileId) {
        return Profile.get({
            id: profileId
        }).$promise.then(function(data) {
            return data.structure;
        });
    }
     //returns all SA-profiles and current as an object
    function getSaProfiles(ip) {
        var sas = [];
        var saProfile =
        {
            entity: "PROFILE_SUBMISSION_AGREEMENT",
            profile: null,
            profiles: [

            ],
        };
        return SA.query({
            pager: 'none'
        }).$promise.then(function (resource) {
            sas = resource;
            saProfile.profiles = [];
            var promises = [];
            sas.forEach(function (sa) {
                saProfile.profiles.push(sa);
                if (ip.submission_agreement == sa.url || (ip.altrecordids && ip.altrecordids["SUBMISSIONAGREEMENT"] == sa.id)){
                    saProfile.profile = sa;
                    saProfile.locked = ip.submission_agreement_locked;
                    if (saProfile.profile.profile_aip) {
                        promises.push(Profile.get({ id: saProfile.profile.profile_aip })
                            .$promise.then(function (resource) {
                                saProfile.profile.profile_aip = resource;
                            }));
                    }
                    if (saProfile.profile.profile_dip) {
                        promises.push(Profile.get({ id: saProfile.profile.profile_dip })
                            .$promise.then(function (resource) {
                                saProfile.profile.profile_dip = resource;
                            }));
                    }
                }
            });
            return $q.all(promises).then(function() {
                return saProfile;
            })
        });
    }

    function getProfileByTypeFromSA(sa, type){
        return sa['profile_' + type];
    }

    function getProfileByTypeFromIP(ip, type){
        return ip['profile_' + type];
    }

    function findProfileByUrl(url, profiles){
        var p = null;

        profiles.forEach(function(profile){
            if (profile.url == url){
                p = profile;
            }
        });

        return p;
    }

    //Ligher fetching of profiles start
    function createProfileObjMinified(type, profiles, ip, sa){
        var required = false;
        var locked = false;
        var checked = false;
        var profile = null;

        p = getProfileByTypeFromSA(sa, type);
        if (p){
            checked = true;
            required = true;
            if (profile == null) {
                profile = p;
            }
        }
        active = profile;
        if(profile) {
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
        if(sa == null) {
            return [];
        }
        if(sa.id != null){
            /*if(ip.profile_transfer_project) {
                selectCollapse.push(createProfileObjMinified("transfer_project", [ip.profile_transfer_project], ip, sa));
            } else {
                selectCollapse.push(createProfileObjMinified("transfer_project", [], ip, sa));
            }
            if(ip.profile_submit_description) {
                selectCollapse.push(createProfileObjMinified("submit_description", [ip.profile_submit_description], ip, sa));
            } else {
                selectCollapse.push(createProfileObjMinified("submit_description", [], ip, sa));
            }
            if(ip.profile_sip) {
                selectCollapse.push(createProfileObjMinified("sip", [ip.profile_sip], ip, sa));
            } else {
                selectCollapse.push(createProfileObjMinified("sip", [], ip, sa));
            }*/
            if(sa.profile_aip) {
                selectCollapse.push(createProfileObjMinified("aip", [sa.profile_aip], ip, sa));
            } else {
                selectCollapse.push(createProfileObjMinified("aip", [], ip, sa));
            }
            if(sa.profile_dip) {
                selectCollapse.push(createProfileObjMinified("dip", [sa.profile_dip], ip, sa));
            } else {
                selectCollapse.push(createProfileObjMinified("dip", [], ip, sa));
            }
            /*
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
        ip.post({
            label: label
        }).$promise.then(function(response) {
            return "created";
        });

    }
    //Returns IP
    function getIp(id) {
        return IP.get({
            id: id
        }).$promise.then(function(data) {
            return data;
        });
    }
    //Returns SA
    function getSa(id) {
        SA.get({
            id: id
        }).$promise.then(function (data) {
            return data;
        });
    }
    //Get list of files in Ip
    function getFileList(ip) {
        return getIp(ip.id).then(function(result) {
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
        return IP.prepareDip({
                label: label,
                object_identifier_value: objectIdentifierValue,
                orders: orders
            }).$promise.then(function (response) {
                return response;
            });
    };

    function createDip(ip) {
        return IP.createDip({ id: ip.id }).$promise.then(function(response) {
            return response;
        });
    }

    function prepareOrder(label) {
        return Order.save( {
            label: label
        }).$promise.then(function(response){
            return response;
        })
    }
    function getWorkareaDir(workareaType, pathStr, pageNumber, pageSize) {
        var sendData;
        if (pathStr == "") {
            sendData = {
                page: pageNumber,
                page_size: pageSize,
                type: workareaType
            };
        } else {
            sendData = {
                page: pageNumber,
                page_size: pageSize,
                path: pathStr,
                type: workareaType
            };
        }

        return $http.get(appConfig.djangoUrl + "workarea-files/",{ params: sendData }).then(function (response) {
            var count = response.headers('Count');
            if (count == null) {
                count = response.data.length;
            }
            if(response.headers()['content-disposition']) {
                return $q.reject(response);
            } else {
                return {
                    numberOfPages: Math.ceil(count/pageSize),
                    data: response.data
                };
            }
        });
    }

    function getDipDir(ip, pathStr, pageNumber, pageSize) {
        if(pathStr == "") {
            sendData = {
                id: ip.id,
                page: pageNumber,
                page_size: pageSize,
            };
        } else {
            sendData = {
                id: ip.id,
                page: pageNumber,
                page_size: pageSize,
                path: pathStr,
            };
        }
        return IP.files(sendData).$promise.then(function(data) {
            var count = data.$httpHeaders('Count');
            if (count == null) {
                count = data.length;
            }
            return {
                numberOfPages: Math.ceil(count/pageSize),
                data: data
            };
        });
    }

    function getDir(ip, pathStr, pageNumber, pageSize) {
        if(pathStr == "") {
            sendData = {
                id: ip.id,
                page: pageNumber,
                page_size: pageSize,
            };
        } else {
            sendData = {
                id: ip.id,
                page: pageNumber,
                page_size: pageSize,
                path: pathStr,
            };
        }
        return IP.files(sendData).$promise.then(function(data) {
            var count = data.$httpHeaders('Count');
            if (count == null) {
                count = data.length;
            }
            return {
                numberOfPages: Math.ceil(count/pageSize),
                data: data
            };
        });
    }
    function addFileToDip(ip, path, file, destination, type) {
        var src = path + file.name;
        var dst = destination + file.name;
        return WorkareaFiles.addToDip({
            dip: ip.id,
            src: src,
            dst: dst,
            type: type
        }).$promise.then(function(response){
            return response;
        });
    }

    function addNewFolder(ip, path, file) {
        return IP.addFile({
            id: ip.id,
            path: path + file.name,
            type: file.type
        }).$promise.then(function(response) {
            return response;
        });
    }

    function addNewWorkareaFolder(workareaType, path, file) {
        return WorkareaFiles.addDirectory({
            type: workareaType,
            path: path + file.name,
        }).$promise.then(function(response) {
            return response;
        });
    }

    function deleteFile(ip, path, file) {
        return IP.removeFile({
            id: ip.id,
            path: path + file.name,
        }).$promise.then(function(response) {
            return response;
        });
    }

    function deleteWorkareaFile(workareaType, path, file) {
        return WorkareaFiles.removeFile({
            type: workareaType,
            path: path + file.name,
        }).$promise.then(function(response) {
            return response;
        });
    }

    function getDir(ip, pathStr, pageNumber, pageSize) {
        if(pathStr == "") {
            sendData = {
                id: ip.id,
                page: pageNumber,
                page_size: pageSize,
            };
        } else {
            sendData = {
                id: ip.id,
                page: pageNumber,
                page_size: pageSize,
                path: pathStr,
            };
        }
        if (ip.state == "At reception" || ip.state == "Prepared") {
            sendData.id = ip.object_identifier_value;
            return IPReception.files(sendData).$promise.then(function(data) {
                var count = data.$httpHeaders('Count');
                if (count == null) {
                    count = data.length;
                }
                return {
                    numberOfPages: Math.ceil(count/pageSize),
                    data: data
                };
            });
        } else {
            return IP.files(sendData).$promise.then(function(data) {
                var count = data.$httpHeaders('Count');
                if (count == null) {
                    count = data.length;
                }
                return {
                    numberOfPages: Math.ceil(count/pageSize),
                    data: data
                };
            });
        }
    }

    function getFile(ip, path, file) {
        return IP.files({
            id: ip.id,
            path: path + file.name,
        }).then(function(response) {
            return response;
        });
    }

    function getWorkareaFile(workareaType, path, file) {
        return WorkareaFiles.files({
            type: workareaType,
            path: path + file.name,
        }).then(function(response) {
            return response;
        });
    }

    /*******************/
    /*HELPER FUNCTIONS*/
    /*****************/

   // Takes an array of steps, expands the ones that should be expanded and
    // populates children recursively.
    function expandAndGetChildren(steps, expandedNodes) {
        var expandedObject = expand(steps, expandedNodes);
        var expanded = expandedObject.expandedSteps;
        steps = expandedObject.steps;
        expanded.forEach(function (item) {
            steps[item.stepIndex] = getChildrenForStep(steps[item.stepIndex], item.number).then(function (stepChildren) {
                var temp = stepChildren;
                temp.children = expandAndGetChildren(temp.children, expandedNodes);
                return temp;
            });
        });
        return steps;
    }

    // Set expanded to true for each item in steps that exists in expandedNodes
    // Returns updated steps and an array containing the expanded nodes
    function expand(steps, expandedNodes) {
        var expanded = [];
        expandedNodes.forEach(function (node) {
            steps.forEach(function (step, idx) {
                if (step.id == node.id) {
                    step.expanded = true;
                    expanded.push({ stepIndex: idx, number: node.page_number });
                }
            });
        });
        return { steps: steps, expandedSteps: expanded };
    }

    // Gets children for a step and processes each child step/task.
    // Returns the updated step
    function getChildrenForStep(step, page_number) {
        page_size = 10;
        if (angular.isUndefined(page_number) || !page_number) {
            step.page_number = 1;
        } else {
            step.page_number = page_number;
        }
        return Step.children({
            id: step.id,
            page: step.page_number,
            page_size: page_size,
            hidden: false
        }).$promise.then(function (resource) {
            var link = linkHeaderParser.parse(resource.$httpHeaders('Link'));
            var count = resource.$httpHeaders('Count');
            if (count == null) {
                count = resource.length;
            }
            step.pages = Math.ceil(count / page_size);
            link.next ? step.next = link.next : step.next = null;
            link.prev ? step.prev = link.prev : step.prev = null;
            step.page_number = page_number || 1;
            var placeholder_removed = false;
            if (resource.length > 0) {
                // Delete placeholder
                step.children.pop();
                placeholder_removed = true;
            }
            var tempChildArray = [];
            resource.forEach(function (child) {
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
            step.children = step.children.map(function (c) {
                c.time_started = $filter('date')(c.time_started, "yyyy-MM-dd HH:mm:ss");
                return c
            });
            if(step.children.length <= 0) {
                step.children = [{ name: "Empty", empty: true }];
            }
            return step;
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
        getWorkareaData: getWorkareaData,
        addFileToDip: addFileToDip,
        addNewFolder: addNewFolder,
        addNewWorkareaFolder: addNewWorkareaFolder,
        deleteFile: deleteFile,
        deleteWorkareaFile: deleteWorkareaFile,
        prepareDip: prepareDip,
        getDipPage: getDipPage,
        getOrderPage: getOrderPage,
        prepareOrder: prepareOrder,
        createDip: createDip,
        getDir: getDir,
        getfile: getFile,
        getWorkareaFile: getWorkareaFile,
    };
});
