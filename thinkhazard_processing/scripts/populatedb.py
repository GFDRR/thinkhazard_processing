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
#

from sqlalchemy import engine_from_config

from thinkhazard_common.models import (
    DBSession,
    AdministrativeDivision,
    )

from .. import settings

from subprocess import call


'''
This script makes it so the database is populated with administrative
divisions. See `populatedb` target in Makefile.
'''


def populate_db():
    connection = DBSession.bind.connect()
    engine_url = DBSession.bind.url

    for i in [0, 1, 2]:
        print "Importing GAUL data for level {}".format(i)
        print "This may take a while"
        sql_file = "g2015_2014_{}.sql".format(i)
        call(["sudo", "-u", "postgres", "psql", "-d", str(engine_url),
              "-f", sql_file])

    trans = connection.begin()
    print "Removing duplicates"
    connection.execute('''
DELETE FROM g2015_2014_0 WHERE gid = 177;
DELETE FROM g2015_2014_2 WHERE gid = 5340;
DELETE FROM g2015_2014_2 WHERE gid = 5382;
DELETE FROM g2015_2014_2 WHERE gid = 5719;
DELETE FROM g2015_2014_2 WHERE gid = 20775;
DELETE FROM g2015_2014_2 WHERE gid = 1059;
''')
    trans.commit()

    print "Creating administrative divs"
    trans = connection.begin()
    connection.execute('''
INSERT INTO datamart.administrativedivision (code, leveltype_id, name,
parent_code, geom)
SELECT adm0_code, 1, adm0_name, NULL, geom
FROM g2015_2014_0;
SELECT DropGeometryColumn('public', 'g2015_2014_0', 'geom');
DROP TABLE g2015_2014_0;''')
    trans.commit()

    trans = connection.begin()
    connection.execute('''
INSERT INTO datamart.administrativedivision (code, leveltype_id, name,
parent_code, geom)
SELECT adm1_code, 2, adm1_name, adm0_code, geom
FROM g2015_2014_1;
SELECT DropGeometryColumn('public', 'g2015_2014_1', 'geom');
DROP TABLE g2015_2014_1;''')
    trans.commit()

    trans = connection.begin()
    connection.execute('''
INSERT INTO datamart.administrativedivision (code, leveltype_id, name,
parent_code, geom)
SELECT adm2_code, 3, adm2_name, adm1_code, geom
FROM g2015_2014_2;
SELECT DropGeometryColumn('public', 'g2015_2014_2', 'geom');
DROP TABLE g2015_2014_2;
''')
    trans.commit()

    trans = connection.begin()
    connection.execute('''
DELETE from datamart.administrativedivision WHERE code in (4375, 426, 10);
''')
    trans.commit()

    print "{} administrative divisions created".format(
        DBSession.query(AdministrativeDivision).count()
    )


def main():
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)

    populate_db()
