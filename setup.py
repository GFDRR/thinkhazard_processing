from setuptools import setup

version = '0.1'

install_requires = [
    ]

setup_requires = [
    ]

tests_require = [
    'nose',
    ]

setup(name='thinkhazard_processing',
      version=version,
      description='ThinkHazard: Overcome Risk - Processing module',
      long_description=open('README.rst').read(),
      url='https://github.com/GFDRR/thinkhazard_processing',
      author='Camptocamp',
      author_email='info@camptocamp.com',
      packages=['thinkhazard_processing'],
      zip_safe=False,
      install_requires=install_requires,
      setup_requires=setup_requires,
      tests_require=tests_require,
      test_suite='thinkhazard_processing.tests',
      )
