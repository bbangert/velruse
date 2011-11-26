from setuptools import setup, find_packages
import sys, os

version = '0.20a1'

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
      packages=['velruse'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'python-openid>=2.2.4',
          'oauth2>=1.1.3',
          'pyramid>=1.2',
          'requests>=0.6.6',
      ],
      tests_require = [
        'nose>=0.11',
      ],
      test_suite='nose.collector',
      entry_points="""
      [paste.app_factory]
      main = velruse.app:make_velruse_app
      """,
      )
