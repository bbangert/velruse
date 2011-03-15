from setuptools import setup, find_packages
import sys, os

version = '0.20'

setup(name='velruse',
      version=version,
      description="Simplifying third-party authentication for web applications.",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='Ben Bangert',
      author_email='ben@groovie.org',
      url='',
      license='',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          "WebOb>=1.0.4",
          "python-openid>=2.2.4",
          "nose>=0.11",
          "oauth2>=1.1.3",
          "pyyaml",
          "beaker",
          "routes",
      ],
      entry_points="""
      [paste.app_factory]
      main = velruse.app:make_velruse_app
      """,
      )
