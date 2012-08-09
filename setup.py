import sys
from setuptools import setup, find_packages

py_version = sys.version_info[:2]

PY3 = py_version[0] == 3

requires=[
    'python-openid',
    'oauth2', # oauth 1.0 support, wtf?
    'pyramid',
    'requests',
    'anykeystore',
]

testing_extras = [
    'selenium',
]

if py_version < (2, 7):
    testing_extras.append('unittest2')

docs_extras = [
    'Sphinx',
    'docutils',
]

setup(name='velruse',
      version='0.3b3',
      description=(
          'Simplifying third-party authentication for web applications.'),
      long_description='',
      # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
          'Development Status :: 4 - Beta',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 2.6',
          'Programming Language :: Python :: 2.7',
          'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
      ],
      keywords='',
      author='Ben Bangert',
      author_email='ben@groovie.org',
      maintainer='Michael Merickel',
      maintainer_email='michael@merickel.org',
      url='http://velruse.readthedocs.org/en/latest/index.html',
      packages=find_packages(
          exclude=['*.tests', '*.tests.*', 'tests.*', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      test_suite='tests',
      extras_require={
          'docs': docs_extras,
          'testing': testing_extras,
      },
      entry_points="""
      [paste.app_factory]
      main = velruse.app:make_app
      """,
      )
