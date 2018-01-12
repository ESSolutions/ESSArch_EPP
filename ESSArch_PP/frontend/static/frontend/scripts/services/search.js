angular.module('myApp').factory('Search', function($http, $sce, appConfig, $translate) {
    var service = {};
    var auth = window.btoa("user:user");
    var headers = { "Authorization": "Basic " + auth };
    var url = appConfig.djangoUrl;
    service.query = function (filters, pageNumber, pageSize) {
        return $http({
            method: 'GET',
            url: url+"search/",
            headers: headers,
            params: angular.extend(
                {
                    page: pageNumber,
                    page_size: pageSize
                },filters)
        }).then(function (response) {
            var returnData = response.data.hits.map(function (item) {
                item._source.id = item._id;
                item._source.name = item._source.name;
                item._source.text = item._source.reference_code + " - " + item._source.title;
                item._source.parent = "#";
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
        return $http.get(url+"search/"+tag.id+"/children/", {headers: headers}).then(function(response) {
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

    return service;
})
