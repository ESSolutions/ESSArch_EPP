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

import versioneer
versioneer.VCS = 'git'
versioneer.versionfile_source = 'ESSArch_EPP/_version.py'
versioneer.versionfile_build = None
versioneer.tag_prefix = '' # tags are like 1.2.0
versioneer.parentdir_prefix = 'ESSArch_EPP-'

try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

if __name__ == '__main__':
    setup(
        name='ESSArch_EPP',
        version=versioneer.get_version(),
        cmdclass=versioneer.get_cmdclass(),
        description='ESSArch Preservation Platform',
        author='Henrik Ek',
        author_email='henrik@essolutions.se',
        url='http://www.essolutions.se',
        install_requires=[
            "MySQL-python>=1.2.3",
            "pyodbc>=3.0.7",
            "pytz>=2013.9",
            "psutil>=1.2.1",
            "billiard>=3.3.0.16",
            "anyjson>=0.3.3",
            "amqp>=1.4.3",
            "kombu>=3.0.12",
            "pycparser>=2.10",
            "cffi>=0.8.6",
            "six>=1.7.3",
            "cryptography>=0.3",
            "pyOpenSSL>=0.14",
            "pysendfile>=2.0.1",
            "nose>=1.1.2",
            "lxml>=3.1.0",
            "pyftpdlib>=1.4.0",
            "Django>=1.6.2",
            "django-picklefield>=0.3.1",
            "argparse>=1.2.1",
            "httplib2>=0.7.5",
            "Jinja2>=2.6",
            "Soapbox>=0.3.7",
            "South>=0.8.4",
            "django.js>=0.8.1",
            "django-eztables>=0.3.2",
            "celery>=3.1.9",
            "django-celery>=3.1.9",
            "jobtastic>=0.2.2",
            "logfileviewer>=0.6.2",
        ],
        packages=find_packages(),
        include_package_data=True,
        zip_safe=False,
    )
