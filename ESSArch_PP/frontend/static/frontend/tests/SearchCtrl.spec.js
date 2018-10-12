'use strict'

describe('SearchCtrl', function() {
    beforeEach(module('essarch.controllers'));
    window.onbeforeunload = jasmine.createSpy();

    var $controller, $scope, controller;

    beforeEach(inject(function(_$controller_){
        $controller = _$controller_;
    }));

    beforeEach(inject(function($rootScope) {
        $scope = $rootScope.$new();
        controller = $controller('SearchCtrl', { $scope: $scope });
    }));

    it('controller defined', function () {
        expect($controller).toBeDefined();
    })
    describe('$state related functionality', function() {
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
});
