"""
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
"""

import versioneer
versioneer.VCS = 'git'
versioneer.versionfile_source = 'ESSArch_PP/_version.py'
versioneer.versionfile_build = None
versioneer.tag_prefix = '' # tags are like 1.2.0
versioneer.parentdir_prefix = 'ESSArch_PP-'

from setuptools import find_packages, setup  
from setuptools.command.install import install as _install  

def _post_install():  
    print 'Running inside _post_install'

class my_install(_install):  
    def run(self):
        _install.run(self)

        # the second parameter, [], can be replaced with a set of parameters if _post_install needs any
        self.execute(_post_install, [],  
                     msg="Running post install task")

if __name__ == '__main__':
    cmdclass=versioneer.get_cmdclass()
    cmdclass.update({'install': my_install})
    setup(
        name='ESSArch_PP',
        version=versioneer.get_version(),
        description='ESSArch Preservation Platform',
        author='Henrik Ek',
        author_email='henrik@essolutions.se',
        url='http://www.essolutions.se',
        install_requires=[
            "ESSArch-Core>=1.1.0.*,<=1.1.1.*",
        ],
        packages=find_packages(),
        include_package_data=True,
        zip_safe=False,
        cmdclass=cmdclass,
    )
