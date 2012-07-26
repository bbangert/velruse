from setuptools import setup, find_packages

requires = [
    'velruse',
    'pyramid',
    'paste',
    'redis',
    'pyramid_debugtoolbar',
    'requests'
]

setup(name='myapp',
      version='0.0',
      description='myapp',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      entry_points="""\
      [paste.app_factory]
      main = myapp:main
      """,
)
