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

    // Get tape slots given robot
    function getTapeSlots(robot) {
        return $http.get(robot.url + "tape-slots/").then(function(response) {
            return response.data;
        });
    }

    // Get tape drives
    function getTapeDrives(robot) {
        return $http.get(robot.url + "tape-drives/").then(function(response) {
            return response.data;
        });
    }

    // Get robots
    function getRobots() {
        return $http.get(appConfig.djangoUrl + 'robots/').then(function(response) {
            return response.data;
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

    function getRobotQueue(robot) {
        var url;
        robot ? url = robot.url + "queue/" : url = appConfig.djangoUrl + "robot-queue/";
        return $http({
            method: 'GET',
            url: url,
        }).then(function(response) {
            return response.data;
        });
    }
    
    function getIoQueue() {
        return $http.get(appConfig.djangoUrl + "io-queue/").then(function(response) {
            return response.data;
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
        return $http.post(appConfig.djangoUrl + "storage-mediums/" + tapeSlot.medium_id + "/mount/").then(function(response) {
            return response;
        });
    }

    function unmountTapeSlot(tapeSlot, force) {
        return $http.post(appConfig.djangoUrl + "storage-mediums/" + tapeSlot.medium_id + "/unmount/", {force: force}).then(function(response) {
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
        getRobotQueue: getRobotQueue,
        getIoQueue: getIoQueue,
        mountTapeDrive: mountTapeDrive,
        unmountTapeDrive: unmountTapeDrive,
        mountTapeSlot: mountTapeSlot,
        unmountTapeSlot: unmountTapeSlot,
    }
});