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
# Author: Arnaud Morvan <arnaud.morvan@camptocamp.com>
#

import sys
from sqlalchemy import engine_from_config

from thinkhazard_common.scripts.initializedb import (
    initdb,
    schema_exists,
    )

from ..models import Base  # NOQA
from .. import settings


def initdb_processing(engine, drop_all=False):
    if not schema_exists(engine, 'processing'):
        engine.execute("CREATE SCHEMA processing;")
    initdb(engine, drop_all=drop_all)


def main(argv=sys.argv):
    engine = engine_from_config(settings, 'sqlalchemy.')
    with engine.begin() as db:
        initdb_processing(db)
