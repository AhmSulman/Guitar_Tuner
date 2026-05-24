from pythonforandroid.recipes.hostpython3 import HostPython3Recipe as _Base


class HostPython3Recipe(_Base):
    # Must match python3 recipe version — p4a checks version parity at build time.
    version = '3.12.7'
    url = 'https://github.com/python/cpython/archive/refs/tags/v{version}.tar.gz'
    patches = ['fix_ensurepip.patch']


recipe = HostPython3Recipe()
