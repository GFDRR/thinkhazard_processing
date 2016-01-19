# -*- coding: utf-8 -*-
#
# Copyright (C) 2015- by the GFDRR / World Bank
#
# This file is part of ThinkHazard.
#
# ThinkHazard is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# ThinkHazard is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# ThinkHazard.  If not, see <http://www.gnu.org/licenses/>.
#
# Author: Pierre Giraud <pierre.giraud@camptocamp.com>
# Author: Arnaud Morvan <arnaud.morvan@camptocamp.com>
# Author: François Van Der Biest <francois.vanderbiest@camptocamp.com>
#

import yaml
from sqlalchemy import engine_from_config
from .. import settings
from ..scripts.initializedb import initdb_processing


local_settings_path = 'local.tests.yaml'

with open(local_settings_path, 'r') as f:
    settings.update(yaml.load(f.read()))


def initdb():
    engine = engine_from_config(settings, 'sqlalchemy.')
    initdb_processing(engine, True)

initdb()
