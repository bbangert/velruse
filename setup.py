from setuptools import setup, find_packages

requires=[
    'python-openid',
    'oauth2',
    'pyramid',
    'requests',
    'anykeystore',
]

testing_extras = [
    'unittest2',
    'nose',
    'nose-testconfig',
    'selenium',
]

docs_extras = [
    'Sphinx',
    'docutils',
]

setup(name='velruse',
      version='1.0.2',
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
      extras_require={
          'docs': docs_extras,
          'testing': testing_extras,
      },
      entry_points="""
      [paste.app_factory]
      main = velruse.app:make_app
      """,
      )
