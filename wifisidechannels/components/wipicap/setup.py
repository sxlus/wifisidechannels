from setuptools import extension, setup
from Cython.Build import cythonize
from numpy import get_include
ext = extension.Extension(name="wipicap", sources=["backends.pyx"], include_dirs=[get_include()])
setup(name = "wipicap", ext_modules = cythonize(ext))
