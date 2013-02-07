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

setup(
    name='ESSArch-GUI',
    version=__version__,
    description='ESSArch GUI',
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
