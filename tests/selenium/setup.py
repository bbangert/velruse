from setuptools import setup

requires = [
    'pyramid',
    'velruse',
]

setup(name='testapp',
      version='0.0',
      packages=['testapp'],
      install_requires=[
          'pyramid',
          'velruse',
          'selenium',
      ],
      entry_points="""\
      [paste.app_factory]
      main = testapp:main
      """,
      )
