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

angular.module('myApp').factory('Resource', function ($q, $filter, $timeout, listViewService, $rootScope, $http, $cookies) {
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
            console.log("eventCollection: ");
            console.log(eventCollection);

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
    function getIpPage(start, number, pageNumber, params, selected, sort, search, state, expandedAics) {
        var ipViewType = $cookies.get('ip-view-type') || 1;
        var sortString = sort.predicate;
        if(sort.reverse) {
            sortString = "-"+sortString;
        }
        var viewType;
        if(ipViewType === "2") {
            viewType = "ip";
        } else {
            viewType = "aic";
        }
            return listViewService.getListViewData(pageNumber, number, $rootScope.navigationFilter, sortString, search, state, viewType).then(function(value) {
                var ipCollection = value.data;
                ipCollection.forEach(function(ip) {
                    ip.collapsed = true;
                    expandedAics.forEach(function(aic, index, array) {
                        if(ip.ObjectIdentifierValue == aic) {
                            ip.collapsed = false;
                            ip.information_packages.forEach(function(information_package, idx, arr) {
                                if(!information_package.ObjectIdentifierValue) {
                                    arr[idx] = $http({
                                        method: 'GET',
                                        url: information_package
                                    }).then(function(response) {
                                        return response.data;
                                    });
                                }
                            });
                        }
                    });
                });

                return {
                    data: ipCollection,
                    numberOfPages: Math.ceil(value.count / number)
                };
            });
    }
    function getReceptionPage(start, number, pageNumber, params, selected, checked, sort, search, state) {
        var sortString = sort.predicate;
        if(sort.reverse) {
            sortString = "-"+sortString;
        }
        return listViewService.getReceptionIps(pageNumber, number, $rootScope.navigationFilter, sortString, search, state).then(function(value) {
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
    return {
        getEventPage: getEventPage,
        getIpPage: getIpPage,
        getReceptionPage: getReceptionPage,
    };

});
