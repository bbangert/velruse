import sys

from setuptools import setup, find_packages

PY3 = sys.version_info[0] >= 3

requires = [
    'pyramid',
    'requests',
    'requests-oauthlib',
    'anykeystore',
]

if PY3:
    requires.append('python3-openid')
else:
    requires.append('python-openid')

testing_extras = [
    'nose',
    'selenium',
    'webtest',
]

docs_extras = [
    'Sphinx',
    'docutils',
]

setup(name='velruse',
      version='1.1.1',
      description=(
          'Simplifying third-party authentication for web applications.'),
      long_description='',
      # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
          'Development Status :: 4 - Beta',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.6',
          'Programming Language :: Python :: 2.7',
#          'Programming Language :: Python :: 3',
#          'Programming Language :: Python :: 3.2',
#          'Programming Language :: Python :: 3.3',
          'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
          'Framework :: Pyramid',
      ],
      keywords='oauth openid social auth facebook google pyramid rest',
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
      tests_require=testing_extras,
      test_suite='nose.collector',
      extras_require={
          'docs': docs_extras,
          'testing': testing_extras,
      },
      entry_points="""
      [paste.app_factory]
      main = velruse.app:make_app
      """,
      )
