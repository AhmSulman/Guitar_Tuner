from pythonforandroid.recipes.numpy import NumpyRecipe as _Base


class NumpyRecipe(_Base):
    patches = (_Base.patches or []) + ['patches/fix_unordered_map.patch']


recipe = NumpyRecipe()
