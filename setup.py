'''
    ESSArch - ESSArch is an Electronic Archive system
    Copyright (C) 2010-2014  ES Solutions AB

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

    Contact information:
    Web - http://www.essolutions.se
    Email - essarch@essolutions.se
'''

__majorversion__ = "2.5"
__revision__ = "$Revision$"
__date__ = "$Date$"
__author__ = "$Author$"
import re
__version__ = '%s.%s' % (__majorversion__,re.sub('[\D]', '',__revision__))


try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

__shortname__ = 'EPP'
__description__ = 'ESSArch Preservation Platform'

if __name__ == '__main__':
    setup(
        name='EPP',
        version=__version__,
        description='ESSArch Preservation Platform',
        author='Henrik Ek',
        author_email='henrik@essolutions.se',
        url='http://www.essolutions.se',
        install_requires=[
            "lxml>=2.2.8",
            "pytz>=2010o",
        ],
        packages=find_packages(),
        include_package_data=True,
        zip_safe=False,
    )
