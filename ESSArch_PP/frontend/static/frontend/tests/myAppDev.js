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

angular.module('myAppDev', ['myApp', 'ngMockE2E']).run(function($httpBackend) {
  var loginToken = 'thisisthelogintoken';
  // returns the current list of phones
  $httpBackend.whenGET(/static/).passThrough();
  $httpBackend.whenPOST(/rest-auth\/login/).respond(function(method, url, data) {
    console.log(data);
    if (data == '{"username":"admin","password":"admin"}') {
      return [200, {key: loginToken}, {}];
    } else {
      return [403, {}, {}];
    }
  });
  $httpBackend.whenGET(/rest-auth\/user/).respond(function(method, url, data) {
    console.log(data);
    var reject = [403, {detail: 'Authentication credentials were not provided.'}, {}];
    var accept = [
      200,
      {
        url: 'http://localhost:8000/api/users/14/',
        id: 14,
        username: 'admin',
        first_name: '',
        last_name: '',
        email: 'admin@essolutions.se',
        groups: [{url: 'http://localhost:8000/api/groups/14/', id: 14, name: 'Admin', permissions: []}],
        is_staff: true,
        is_active: true,
        is_superuser: false,
        last_login: '2017-01-12T13:31:18Z',
        date_joined: '2016-12-08T15:19:21Z',
        permissions: [],
        user_permissions: [],
      },
      {},
    ];
    if (true) {
      return accept;
    } else {
      return reject;
    }
  });
});
