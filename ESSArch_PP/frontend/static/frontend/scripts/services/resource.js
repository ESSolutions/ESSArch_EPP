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

angular.module('myApp').factory('Resource', function ($q, $filter, $timeout, listViewService, $rootScope, $http, $cookies, $window) {
    //Get data for Events table
	function getEventPage(start, number, pageNumber, params, selected, sort) {
        var sortString = sort.predicate;
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
    function getIpPage(start, number, pageNumber, params, selected, sort, search, state, expandedAics, columnFilters) {
        var viewType = $window.sessionStorage["view-type"] || 'aic';
        var sortString = sort.predicate;
        if(sort.reverse) {
            sortString = "-"+sortString;
        }
        return listViewService.getListViewData(pageNumber, number, $rootScope.navigationFilter, sortString, search, state, viewType, columnFilters).then(function(value) {
            var ipCollection = value.data;
            ipCollection.forEach(function(ip) {
                ip.collapsed = true;
                expandedAics.forEach(function(aic, index, array) {
                    if(ip.ObjectIdentifierValue == aic) {
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
    function getReceptionPage(start, number, pageNumber, params, selected, checked, sort, search, state, columnFilters) {
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
                if(selected.id == ip.id) {
                    ip.class = "selected";
                }
            });
            
            return {
                data: ipCollection,
                numberOfPages: Math.ceil(value.count / number)
            };
        });
    }
    function getStorageMediums(start, number, pageNumber, params, selected, sort, search) {
        var sortString = sort.predicate;
        if(sort.reverse) {
            sortString = "-"+sortString;
        }
        return listViewService.getStorageMediums(pageNumber, number, $rootScope.navigationFilter, sortString, search).then(function(value) {
            var storageMediumCollection = value.data;
            storageMediumCollection.forEach(function(medium){
                if(selected.id == medium.id) {
                    medium.class = "selected";
                }
            });
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
        return listViewService.getStorageObjects(pageNumber, number, medium, sortString, search).then(function(value) {
            var storageObjectCollection = value.data;
            return {
                data: storageObjectCollection,
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
    };
    
});
