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

angular.module('myApp').factory('Resource', function ($q, $filter, $timeout, listViewService, Storage, $rootScope, $http, $cookies, $window) {
    //Get data for Events table
	function getEventPage(start, number, pageNumber, params, selected, sort) {
        var sortString = sort.predicate;
        if(sort.predicate == "eventDateTime") {
            sortString = sortString + ",-id";
        }
        if(sort.reverse) {
            sortString = "-"+sortString;
        }
        return listViewService.getEvents($rootScope.ip, pageNumber, number, sortString).then(function(value) {
            var eventCollection = value.data;
            eventCollection.forEach(function(event) {
                selected.forEach(function(item) {
                    if(item.id == event.id) {
                        event.class = "selected";
                    }
                });
            });
            /*

            var filtered = params.search.predicateObject ? $filter('filter')(eventCollection, params.search.predicateObject) : eventCollection;

            if (params.sort.predicate) {
                filtered = $filter('orderBy')(filtered, params.sort.predicate, params.sort.reverse);
            }

            var result = filtered.slice(start, start + number);
            */

            return {
                data: eventCollection,
                numberOfPages: Math.ceil(value.count / number)
            };
        });
	}
    //Get data for IP table
    function getIpPage(start, number, pageNumber, params, sort, search, state, expandedAics, columnFilters, archived, workarea) {
        var viewType = $window.sessionStorage["view-type"] || 'aic';
        var sortString = sort.predicate;
        if(sort.reverse) {
            sortString = "-"+sortString;
        }
        return listViewService.getListViewData(pageNumber, number, $rootScope.navigationFilter, sortString, search, state, viewType, columnFilters, archived, workarea).then(function(value) {
            var ipCollection = value.data;
            ipCollection.forEach(function(ip) {
                ip.collapsed = true;
                expandedAics.forEach(function(aic, index, array) {
                    if(ip.object_identifier_value == aic) {
                        ip.collapsed = false;
                    }
                });
            });

            return {
                data: ipCollection,
                numberOfPages: Math.ceil(value.count / number)
            };
        });
    }

    function getWorkareaIps(workarea, start, number, pageNumber, params, sort, search, expandedAics, columnFilters) {
        var viewType = $window.sessionStorage["view-type"] || 'aic';
        var sortString = sort.predicate;
        if(sort.reverse) {
            sortString = "-"+sortString;
        }
        return listViewService.getWorkareaData(workarea, pageNumber, number, $rootScope.navigationFilter, sortString, search, viewType, columnFilters).then(function(value) {
            var ipCollection = value.data;
            ipCollection.forEach(function(ip) {
                ip.collapsed = true;
                expandedAics.forEach(function(aic, index, array) {
                    if(ip.object_identifier_value == aic) {
                        ip.collapsed = false;
                    }
                });
            });
            return {
                data: ipCollection,
                numberOfPages: Math.ceil(value.count / number)
            };
        });
    }

    function getDips(start, number, pageNumber, params, sort, search, columnFilters) {
        var sortString = sort.predicate;
        if(sort.reverse) {
            sortString = "-"+sortString;
        }
        return listViewService.getDipPage(pageNumber, number, $rootScope.navigationFilter, sortString, search, columnFilters).then(function(value) {
            var ipCollection = value.data;
            ipCollection.forEach(function(ip) {
                ip.collapsed = false;
            });
            return {
                data: ipCollection,
                numberOfPages: Math.ceil(value.count / number)
            };
        });
    }

    function getOrders(start, number, pageNumber, params, sort, search) {
        var sortString = sort.predicate;
        if(sort.reverse) {
            sortString = "-"+sortString;
        }
        return listViewService.getOrderPage(pageNumber, number, $rootScope.navigationFilter, sortString, search).then(function(value) {
            var ipCollection = value.data;
            ipCollection.forEach(function(ip) {
                ip.collapsed = false;
            });
            return {
                data: ipCollection,
                numberOfPages: Math.ceil(value.count / number)
            };
        });
    }

    function getReceptionPage(start, number, pageNumber, params, checked, sort, search, state, columnFilters) {
        var sortString = sort.predicate;
        if(sort.reverse) {
            sortString = "-"+sortString;
        }
        return listViewService.getReceptionIps(pageNumber, number, $rootScope.navigationFilter, sortString, search, state, columnFilters).then(function(value) {
            var ipCollection = value.data;
            ipCollection.forEach(function(ip) {
                ip.checked = false;
                checked.forEach(function(checkedIp) {
                    if(ip.id == checkedIp.id) {
                        ip.checked = true;
                    }
                });
            });

            return {
                data: ipCollection,
                numberOfPages: Math.ceil(value.count / number)
            };
        });
    }

    // Storage

    function getStorageMediums(start, number, pageNumber, params, sort, search) {
        var sortString = sort.predicate;
        if(sort.reverse) {
            sortString = "-"+sortString;
        }
        return Storage.getStorageMediums(pageNumber, number, $rootScope.navigationFilter, sortString, search).then(function(value) {
            var storageMediumCollection = value.data;
            return {
                data: storageMediumCollection,
                numberOfPages: Math.ceil(value.count / number)
            };
        });
    }
    function getStorageObjects(start, number, pageNumber, params, medium, sort, search) {
        var sortString = sort.predicate;
        if(sort.reverse) {
            sortString = "-"+sortString;
        }
        return Storage.getStorageObjects(pageNumber, number, medium, sortString, search).then(function(value) {
            var storageObjectCollection = value.data;
            return {
                data: storageObjectCollection,
                numberOfPages: Math.ceil(value.count / number)
            };
        });
    }

    function getRobots(start, number, pageNumber, params, sort, search) {
        var sortString = sort.predicate;
        if (sort.reverse) {
            sortString = "-" + sortString;
        }
        return Storage.getRobots(pageNumber, number, sortString, search).then(function (value) {
            var robotCollection = value.data;
            return {
                data: robotCollection,
                numberOfPages: Math.ceil(value.count / number)
            };
        });
    }

    function getRobotQueue(start, number, pageNumber, params, sort, search) {
        var sortString = sort.predicate;
        if (sort.reverse) {
            sortString = "-" + sortString;
        }
        return Storage.getRobotQueue(pageNumber, number, sortString, search).then(function (value) {
            var robotQueueCollection = value.data;
            return {
                data: robotQueueCollection,
                numberOfPages: Math.ceil(value.count / number)
            };
        });
    }

    function getRobotQueueForRobot(start, number, pageNumber, params, sort, search, robot) {
        var sortString = sort.predicate;
        if (sort.reverse) {
            sortString = "-" + sortString;
        }
        return Storage.getRobotQueueForRobot(pageNumber, number, sortString, search, robot).then(function (value) {
            var robotQueueCollection = value.data;
            return {
                data: robotQueueCollection,
                numberOfPages: Math.ceil(value.count / number)
            };
        });
    }

    function getIoQueue(start, number, pageNumber, params, sort, search) {
        var sortString = sort.predicate;
        if (sort.reverse) {
            sortString = "-" + sortString;
        }
        return Storage.getIoQueue(pageNumber, number, sortString, search).then(function (value) {
            var ioQueueCollection = value.data;
            return {
                data: ioQueueCollection,
                numberOfPages: Math.ceil(value.count / number)
            };
        });
    }

    function getTapeDrives(start, number, pageNumber, params, sort, search, robot) {
        var sortString = sort.predicate;
        if (sort.reverse) {
            sortString = "-" + sortString;
        }
        return Storage.getTapeDrives(pageNumber, number, sortString, search, robot).then(function (value) {
            var tapeDrivecollection = value.data;
            return {
                data: tapeDrivecollection,
                numberOfPages: Math.ceil(value.count / number)
            };
        });
    }

    function getTapeSlots(start, number, pageNumber, params, sort, search, robot) {
        var sortString = sort.predicate;
        if (sort.reverse) {
            sortString = "-" + sortString;
        }
        return Storage.getTapeSlots(pageNumber, number, sortString, search, robot).then(function (value) {
            var tapeSlotCollection = value.data;
            return {
                data: tapeSlotCollection,
                numberOfPages: Math.ceil(value.count / number)
            };
        });
    }
    return {
        getEventPage: getEventPage,
        getIpPage: getIpPage,
        getReceptionPage: getReceptionPage,
        getStorageMediums: getStorageMediums,
        getStorageObjects: getStorageObjects,
        getWorkareaIps: getWorkareaIps,
        getDips: getDips,
        getOrders: getOrders,
        getRobots: getRobots,
        getRobotQueue: getRobotQueue,
        getRobotQueueForRobot: getRobotQueueForRobot,
        getIoQueue: getIoQueue,
        getTapeDrives: getTapeDrives,
        getTapeSlots: getTapeSlots,
    };
});
