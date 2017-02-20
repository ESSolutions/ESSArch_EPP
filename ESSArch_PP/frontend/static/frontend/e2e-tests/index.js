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

'use strict';

describe('my app', function() {
    beforeEach(function() {
      browser.get('/');
    });

	it('should automatically redirect to /login when location hash/fragment is empty and not logged in', function() {
		expect(browser.getLocationAbsUrl()).toMatch("/login");
	});

	it('should render login box when user navigates to /login', function() {
		expect($('.login-box').isPresent()).toBe(true);
	});
});
