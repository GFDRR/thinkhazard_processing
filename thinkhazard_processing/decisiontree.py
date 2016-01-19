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

from thinkhazard_common.models import (
    DBSession,
    AdminLevelType,
    )


def apply_decision_tree(dry_run=False):
    connection = DBSession.bind.connect()
    trans = connection.begin()
    try:
        print "Purging previous relations"
        connection.execute(clearall_query())
        print "Calculating level REG"
        connection.execute(level_REG_query())
        print "Upscaling to PRO"
        connection.execute(upscaling_query(u'PRO'))
        print "Upscaling to COU"
        connection.execute(upscaling_query(u'COU'))
        if dry_run:
            trans.rollback()
        else:
            trans.commit()
    except:
        trans.rollback()
        raise


def clearall_query():
    return '''
DELETE FROM datamart.rel_hazardcategory_administrativedivision;
'''


def level_REG_query():
    return '''
INSERT INTO datamart.rel_hazardcategory_administrativedivision (
    administrativedivision_id,
    hazardcategory_id,
    source
)
SELECT DISTINCT
    output.admin_id AS administrativedivision_id,
    first_value(category.id) OVER w AS hazardcategory_id,
    first_value(set.id) OVER w AS source
FROM
    processing.output AS output
    JOIN processing.hazardset AS set
        ON set.id = output.hazardset_id
    JOIN datamart.hazardcategory AS category
        ON category.hazardtype_id = set.hazardtype_id
        AND category.hazardlevel_id = output.hazardlevel_id
WINDOW w AS (
    PARTITION BY
        output.admin_id,
        set.hazardtype_id
    ORDER BY
        set.calculation_method_quality DESC,
        set.scientific_quality DESC,
        set.local DESC,
        set.data_lastupdated_date DESC
);
'''


def upscaling_query(level):
    return '''
INSERT INTO datamart.rel_hazardcategory_administrativedivision (
    administrativedivision_id,
    hazardcategory_id,
    source
)
SELECT DISTINCT
    admindiv_parent.id AS administrativedivision_id,
    first_value(category.id) OVER w AS hazardcategory_id,
    first_value(category_admindiv.source) OVER w AS source
FROM
    datamart.rel_hazardcategory_administrativedivision AS category_admindiv
    JOIN datamart.hazardcategory AS category
        ON category.id = category_admindiv.hazardcategory_id
    JOIN datamart.enum_hazardlevel AS level
        ON level.id =  category.hazardlevel_id
    JOIN datamart.administrativedivision AS admindiv_child
        ON admindiv_child.id = category_admindiv.administrativedivision_id
    JOIN datamart.administrativedivision AS admindiv_parent
        ON admindiv_parent.code = admindiv_child.parent_code
WHERE admindiv_parent.leveltype_id = {}
WINDOW w AS (
    PARTITION BY
        admindiv_parent.id,
        category.hazardtype_id
    ORDER BY
        level.order
);
'''.format(AdminLevelType.get(level).id)
