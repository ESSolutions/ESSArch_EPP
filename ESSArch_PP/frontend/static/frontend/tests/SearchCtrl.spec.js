'use strict'

describe('SearchCtrl', function() {
    beforeEach(module('essarch.controllers'));

    var $controller, $scope, controller, Search, $translate;

    beforeEach(inject(function(_$controller_){
        $controller = _$controller_;
    }));

    Search = jasmine.createSpyObj('Search', [
        'addNode',
    ]);

    $translate = jasmine.createSpyObj('$translate', [
        'instant',
    ]);

    module(function ($provide) {
        $provide.value('Search', Search);
        $provide.value('$translate', $translate);
    });

    beforeEach(inject(function($rootScope) {
        $scope = $rootScope.$new();
        controller = $controller('SearchCtrl', { $scope: $scope, Search: Search, $translate: $translate });
    }));

    it('controller defined', function () {
        expect($controller).toBeDefined();
    })
    describe('goToDetailView', function() {
        beforeEach(inject(function($state, $rootScope) {
            this.test = null;
            spyOn($state, 'go').and.callFake(function($state, params) {
                this.test = $state;
            })
            $rootScope.latestRecord = { _index: 'index1', _id: 'id1'};
            controller.goToDetailView();
        }))
        it('state.go is called', inject(function($state){
            expect($state.go).toHaveBeenCalled();
        }))
        it('state.go is called with correct parameters', inject(function($state){
            expect($state.go).toHaveBeenCalledWith('home.access.search.index1', {id: 'id1'});
        }))
    })
    describe('vm.createArchive', function() {
        beforeEach(inject(function($q) {
            var SearchPromise = {
                addNode: $q.defer()
            };

            Search.addNode.and.returnValue(SearchPromise.addNode.promise);

            SearchPromise.addNode.resolve({
                "data": {id: "node1"},
            });
            controller.archiveName = 'name';
            controller.structureName = 'structure';
            controller.nodeType = 'type';
            controller.referenceCode = 'reference_code';
            $scope.$apply(function () {
                controller.createArchive(
                    controller.archiveName,
                    controller.structureName,
                    controller.nodeType,
                    controller.referenceCode
                );
            });
        }))
        it('Search.addNode is called', function(){
            expect(Search.addNode).toHaveBeenCalled();
        })
        it('variables reset', function(){
            [
                controller.archiveName,
                controller.structureName,
                controller.nodeType,
                controller.referenceCode
            ].forEach(function(x) {
                expect(x).toBeNull();
            })
        })
    })
    describe('vm.calculatePageNumber', function() {
        beforeEach(inject(function() {
            $translate.instant.and.returnValue('translate');
        }))
        it('page 1, 25/page and 50 total', function() {
            controller.tableState = {"sort":{},"search":{},"pagination":{"start":0,"number":25}};
            controller.searchResult = new Array(25);
            controller.numberOfResults = 50;
            var pageNumberString = controller.calculatePageNumber();
            expect(pageNumberString).toBe('translate 1-25 translate 50');
        })
        it('page 2, 25/page and 50 total', function() {
            controller.tableState = {"sort":{},"search":{},"pagination":{"start":25,"number":25}};
            controller.searchResult = new Array(25);
            controller.numberOfResults = 50;
            var pageNumberString = controller.calculatePageNumber();
            expect(pageNumberString).toBe('translate 26-50 translate 50');
        })
        it('page 1, 16/page and 16 total', function() {
            controller.tableState = {"sort":{},"search":{},"pagination":{"start":0,"number":16}};
            controller.searchResult = new Array(16);
            controller.numberOfResults = 16;
            var pageNumberString = controller.calculatePageNumber();
            expect(pageNumberString).toBe('translate 1-16 translate 16');
        })
    })
    describe('vm.clearSearch', function() {
        beforeEach(inject(function() {
            controller.filterObject.q = "search";
            controller.includedTypes.ip = false;
            controller.extensionFilter['xml'] = true;
        }))
        it('search term reset', function() {
            controller.clearSearch();
            expect(controller.filterObject.q).toBe("");
        })
        it('included types reset', function() {
            controller.clearSearch();
            expect(controller.includedTypes).toEqual({
                archive: true,
                ip: true,
                component: true,
                file: true
            });
        })
        it('extension filter reset', function() {
            controller.clearSearch();
            expect(controller.extensionFilter).toEqual({});
        })
        it('page_size default 25', function() {
            controller.clearSearch();
            expect(controller.filterObject.page_size).toBe(25);
        })
        it('page size set to vm.resultsPerPage', function() {
            controller.resultsPerPage = 10;
            controller.clearSearch();
            expect(controller.filterObject.page_size).toBe(10);
        })
    })
    describe('formatFilters', function() {
        beforeEach(inject(function() {
            controller.includedTypes = {
                archive: true,
                ip: true,
                component: true,
                file: true
            }
        }))
        it('include all default types', function() {
            controller.formatFilters();
            expect(controller.filterObject.indices).toBe("archive,ip,component,file");
        })
        it('include archive, file and test', function() {
            controller.includedTypes.ip = false;
            controller.includedTypes.component = false;
            controller.includedTypes.test = true;
            controller.formatFilters();
            expect(controller.filterObject.indices).toBe("archive,file,test");
        })
    })
});
