
from setuptools import setup, find_packages

from pytml.version import __version__

PROJECT = "pytml"

setup(name=PROJECT,
      version = __version__,
      packages = find_packages(),
      description = "mix Python and HTML",
      author = "Barry Rowlingson",
      author_email = "B.Rowlingson@gmail.com",
      entry_points={
          'console_scripts': [
            'pytml = pytml.extract_python:main'
            ]
          },
      license = "MIT",
)

