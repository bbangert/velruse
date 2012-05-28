from setuptools import setup, find_packages

requires=[
    'python-openid',
    'oauth2',
    'pyramid',
    'requests',
    'anykeystore',
]

tests_require = requires + [
    'nose',
    'nose-testconfig',
    'selenium',
]

setup(name='velruse',
      version='0.3dev',
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
      maintainer_email='oss@m.merickel.org',
      url='velruse.readthedocs.org',
      packages=find_packages(
          exclude=['*.tests', '*.tests.*', 'tests.*', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      extras_require={
          'testing': tests_require,
      },
      entry_points="""
      [paste.app_factory]
      main = velruse.app:make_velruse_app
      """,
      )
