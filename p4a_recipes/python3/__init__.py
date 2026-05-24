from pythonforandroid.recipes.python3 import Python3Recipe as _Base


class Python3Recipe(_Base):
    # Pin to Python 3.12 — Kivy 2.3.0's Cython-generated C code uses
    # _PyInterpreterState_GetConfig which changed incompatibly in Python 3.13+.
    version = '3.12.7'
    url = 'https://github.com/python/cpython/archive/refs/tags/v{version}.tar.gz'
    patches = [
        'patches/pyconfig_detection.patch',
        'patches/reproducible-buildinfo.diff',
    ]


recipe = Python3Recipe()
