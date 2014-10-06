__shortname__ = 'EPP'
__description__ = 'ESSArch Preservation Platform'

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions
