angular.module('myApp').factory('Search', function($http, $sce, appConfig, $translate) {
    var service = {};
    var url = appConfig.djangoUrl;
    service.query = function (filters, pageNumber, pageSize) {
        return $http({
            method: 'GET',
            url: url+"search/",
            params: angular.extend(
                {
                    page: pageNumber,
                    page_size: pageSize
                },filters)
        }).then(function (response) {
            var returnData = response.data.hits.map(function (item) {
                item._source.id = item._id;
                item._source.name = item._source.name;
                item._source.text = item._source.reference_code + " - " + item._source.name;
                item._source.parent = "#";
                item._source._index = item._index;
                if(item._index == "archive") {
                    item._source.type = $translate.instant("ARCHIVE");
                }
                for (var key in item.highlight) {
                    item._source[key] = $sce.trustAsHtml(item.highlight[key][0]);
                }
                return item._source;
            });
            var count = response.headers('Count');
            if (count == null) {
                count = response.data.length;
            }
            return {
                numberOfPages: Math.ceil(count / pageSize),
                count: count,
                data: returnData,
                aggregations: response.data.aggregations
            };
        });
    }

    service.getChildrenForTag = function(tag){
        return $http.get(url+"search/"+tag.id+"/children/").then(function(response) {
            var temp  = response.data.map(function(item) {
                item._source.id = item._id;
                item._source.text = item._source.reference_code + " - "+item._source.name;
                return item._source;
            });
            return temp;
        })
    }
    service.tags = function() {

    }

    service.updateNode = function(node, data, refresh) {
        if(angular.isUndefined(refresh)) {
            refresh = false;
        }
        return $http({
            method: 'PATCH',
            url: url+"search/"+node._index + "/" + node._id + "/",
            params: {
                refresh: refresh
            },
            data: data
        }).then(function(response) {
            return response;
        });
    }
    service.addNode = function(node) {
        return $http({
            method: 'POST',
            url: url+"search/",
            params: { refresh: true },
            data: node
        }).then(function(response) {
            return response;
        });
    }
    service.createNewVersion = function(node) {
        return $http({
            method: 'POST',
            url: url+"search/"+node._index + "/" + node._id + "/new-version/",
            params: { refresh: true },
        }).then(function(response) {
            return response;
        });
    }
    service.createNewStructure = function(node, data) {
        return $http({
            method: 'POST',
            url: url + "search/" + node._index + "/" + node._id + "/new-structure/",
            params: { refresh: true },
            data: data
        }).then(function(response) {
            return response;
        })
    }
    service.removeNode = function(node) {
        return $http({
            method: 'DELETE',
            url: url+"search/"+node._index + "/" + node._id + "/",
            params: { refresh: true },
        }).then(function(response) {
            return response;
        });
    }
    service.setAsCurrentVersion = function (node, refresh) {
        return $http({
            method: 'PATCH',
            url: url + "search/" + node._index + "/" + node._id + "/set-as-current-version/",
            params: {
                refresh: refresh
            },
        }).then(function (response) {
            return response;
        });
    }
    return service;
})
