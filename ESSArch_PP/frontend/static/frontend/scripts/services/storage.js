angular.module('myApp').factory('Storage', function($http, $q, appConfig) {

    // Get storage mediums
    function getStorageMediums(pageNumber, pageSize, filters, sortString, searchString) {
        return $http({
            method: 'GET',
            url: appConfig.djangoUrl + "storage-mediums/",
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
    }

    // Get storage objects given storage medium
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


    // Get robots
    function getRobots(pageNumber, pageSize, sortString, searchString) {
        return $http({
            method: 'GET',
            url: appConfig.djangoUrl + 'robots/',
            params: {
                page: pageNumber,
                page_size: pageSize,
                ordering: sortString,
                search: searchString,
            }
        }).then(function (response) {
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

    // Get tape slots given robot
    function getTapeSlots(pageNumber, pageSize, sortString, searchString, robot) {
        return $http({
            method: 'GET',
            url: robot.url + "tape-slots/",
            params: {
                page: pageNumber,
                page_size: pageSize,
                ordering: sortString,
                search: searchString,
            }
        }).then(function (response) {
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

    // Get tape drives
    function getTapeDrives(pageNumber, pageSize, sortString, searchString, robot) {
        return $http({
            method: 'GET',
            url: robot.url + "tape-drives/",
            params: {
                page: pageNumber,
                page_size: pageSize,
                ordering: sortString,
                search: searchString,
            }
        }).then(function (response) {
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


    function getRobotQueueForRobot(pageNumber, pageSize, sortString, searchString, robot) {
        var url = robot.url + "queue/";
        return $http({
            method: 'GET',
            url: url,
            params: {
                page: pageNumber,
                page_size: pageSize,
                ordering: sortString,
                search: searchString,
            }
        }).then(function (response) {
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

    function getRobotQueue(pageNumber, pageSize, sortString, searchString) {
        var url = appConfig.djangoUrl + "robot-queue/";
        return $http({
            method: 'GET',
            url: url,
            params: {
                page: pageNumber,
                page_size: pageSize,
                ordering: sortString,
                search: searchString,
            }
        }).then(function (response) {
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

    function getIoQueue(pageNumber, pageSize, sortString, searchString) {
        return $http({
            method: 'GET',
            url: appConfig.djangoUrl + "io-queue/",
            params: {
                page: pageNumber,
                page_size: pageSize,
                ordering: sortString,
                search: searchString,
            }
        }).then(function (response) {
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

    // Inventory robot
    function inventoryRobot(robot) {
        return $http.post(robot.url + "inventory/").then(function(response) {
            return response;
        }).catch(function(response) {
            return response.statusText;
        });
    }

    function mountTapeDrive(tapeDrive, medium) {
        return $http.post(tapeDrive.url + "mount/", {storage_medium: medium.id}).then(function(response) {
            return response;
        });
    }

    function unmountTapeDrive(tapeDrive, force) {
        return $http.post(tapeDrive.url + "unmount/", {force: force}).then(function(response) {
            return response;
        });
    }

    function mountTapeSlot(tapeSlot, medium) {
        return $http.post(appConfig.djangoUrl + "storage-mediums/" + tapeSlot.storage_medium.id + "/mount/").then(function(response) {
            return response;
        });
    }

    function unmountTapeSlot(tapeSlot, force) {
        return $http.post(appConfig.djangoUrl + "storage-mediums/" + tapeSlot.storage_medium.id + "/unmount/", {force: force}).then(function(response) {
            return response;
        });
    }
    return {
        getStorageMediums: getStorageMediums,
        getStorageObjects: getStorageObjects,
        getTapeSlots: getTapeSlots,
        getTapeDrives: getTapeDrives,
        getRobots: getRobots,
        inventoryRobot: inventoryRobot,
        getRobotQueueForRobot: getRobotQueueForRobot,
        getRobotQueue: getRobotQueue,
        getIoQueue: getIoQueue,
        mountTapeDrive: mountTapeDrive,
        unmountTapeDrive: unmountTapeDrive,
        mountTapeSlot: mountTapeSlot,
        unmountTapeSlot: unmountTapeSlot,
    }
});