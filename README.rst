ThinkHazard: Overcome Risk - Processing module
##############################################

.. image:: https://api.travis-ci.org/GFDRR/thinkhazard_processing.svg?branch=master
    :target: https://travis-ci.org/GFDRR/thinkhazard_processing
    :alt: Travis CI Status

This module is intended to work together with the ThinkHazard module.

Getting Started
===============

Create a Python virtual environment and install the project into it::

    $ make install
    
Create a database and then populate it with::

    $ make initdb

For more options, see::

    $ make help

Configure using thinkhazard_processing.yaml
===========================================

Keys in configuration file:

sqlalchemy.url
--------------

Database connection parameters, example:

.. code:: yaml

    sqlalchemy.url: postgresql://www-data:www-data@localhost:5432/thinkhazard_processing

data_path
---------

Path to main data folder, example:

.. code:: yaml

    data_path: /var/sig

For production, we recommend a dedicated disk partition.

hazard_types
------------

Harvesting and processing configuration for each hazard type.
One entry for each hazard type mnemonic.

Possible subkeys include the following:

- ``hazard_type``: Corresponding hazard_type value in geonode.

- ``return_periods``: One entry per hazard level mnemonic with
  corresponding return periods. Each return period can be a value or a list
  with minimum and maximum values, example:

  .. code:: yaml

      return_periods:
        HIG: [10, 25]
        MED: 50
        LOW: [100, 1000]

- ``thresholds``: Flexible threshold configuration.

  This can be a simple and global value per hazardtype. Example:

  .. code:: yaml

       thresholds: 1700

  But it can also contain one or many sublevels for complex configurations:

  1) ``global`` and ``local`` entries for corresponding hazardsets.
  2) One entry per hazard level mnemonic.
  3) One entry per hazard unit from geonode.

  Example:

  .. code:: yaml

       thresholds:
         global:
           HIG:
             unit1: value1
             unit2: value2
           MED:
             unit1: value1
             unit2: value2
           LOW:
             unit1: value1
             unit2: value2
         local:
           unit1: value1
           unit2: value2

- ``values``: One entry per hazard level,
  with list of corresponding values in preprocessed layer.
  If present, the layer is considered as preprocessed, and the above
  ``thresholds`` and ``return_periods`` are not taken into account.
  Example:

  .. code:: yaml

      values:
        HIG: [103]
        MED: [102]
        LOW: [101]
        VLO: [100, 0]

Use ``local_settings.yaml``
===========================

The settings defined in the ``thinkhazard_processing.yaml`` file can be
overriden by creating a ``local_settings.yaml`` file at the root of the
project.

For example, you can define a specific database connection with a
``local_settings.yaml`` file that looks like this::

    sqlalchemy.url: postgresql://www-data:www-data@localhost:9999/thinkhazard

Processing tasks
================

Thinkhazard_processing provides several consecutive tasks to populate the
thinkhazard datamart database. These are:

``.build/venv/bin/harvest [--force] [--dry-run]``

Havest metadata from geonode, create HazardSet and Layer records.

``.build/venv/bin/download [--title] [--force] [--dry-run]``

Download raster files in data folder.

``.build/venv/bin/complete [--force] [--dry-run]``

Check hazardsets that are complete, calculate some fields and pin them as
complete.

``.build/venv/bin/process [--hazarset_id ...] [--force] [--dry-run]``

Calculate output from hazardsets and administrative divisions.

``.build/venv/bin/decision_tree [--force] [--dry-run]``

Apply the decision tree followed by upscaling on process outputs to get the final
relations between administrative divisions and hazard categories.

Run tests
=========

Prior to running the tests, one has to create a dedicated database, 
eg. thinkhazard_tests, and register it with::

    $ echo "sqlalchemy.url: postgresql://www-data:www-data@localhost/thinkhazard_tests" > local.tests.yaml

Run the tests with the following command::

    $ make test
