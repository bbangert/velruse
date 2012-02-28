from setuptools import setup, find_packages

version = '0.3.wiggy.2dev'

tests_require = [
    'nose>=0.11',
    'selenium',
    'pymongo',
    'unittest2',
    'PasteScript',
]

setup(name='velruse',
      version=version,
      description=(
          'Simplifying third-party authentication for web applications.'),
      long_description='',
      # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[],
      keywords='',
      author='Ben Bangert',
      author_email='ben@groovie.org',
      url='',
      license='',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'python-openid>=2.2.4',
          'oauth2>=1.1.3',
          'pyramid>=1.2',
          'requests>=0.6.6',
      ],
      tests_require=tests_require,
      extras_require={'tests': tests_require},
      entry_points="""
      [paste.app_factory]
      main = velruse.app:make_velruse_app
      """,
      )
