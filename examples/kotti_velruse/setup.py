from setuptools import setup, find_packages
import os

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()

version = '0.1'

requires = [
    'Kotti',
    'kotti_velruse',
    ]

setup(name='kotti_velruse',
      version=version,
      description="Kotti authentication with Velruse: OpenID, OAuth2, Google, Yahoo, Live, Facebook, Twitter and others",
      long_description=README,
      classifiers=[
          "Programming Language :: Python",
          "Framework :: Pyramid",
          "Topic :: Internet :: WWW/HTTP",
          "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
      ],
      keywords='kotti authentication velruse openid oauth2 google yahoo live facebook twitter',
      author='Richard Gomes',
      author_email='rgomes.info@gmail.com',
      url='http://kotti_velruse.readthedocs.org',
      license='BSD',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      )
