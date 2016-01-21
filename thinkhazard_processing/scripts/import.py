import transaction
import csv
from subprocess import call

from sqlalchemy import engine_from_config

from thinkhazard_common.models import (
    DBSession,
    AdministrativeDivision,
    ClimateChangeRecommendation,
    HazardType,
    HazardLevel,
    HazardCategory,
    HazardCategoryTechnicalRecommendationAssociation,
    TechnicalRecommendation,
    )

from .. import settings


def import_admindivs():
    '''
    This script makes it so the database is populated with administrative
    divisions.
    '''

    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)

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


def import_recommendations():
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)

    with transaction.manager:

        DBSession.query(HazardCategoryTechnicalRecommendationAssociation) \
            .delete()
        DBSession.query(TechnicalRecommendation).delete()

        # First load general recommendations

        with open('data/general_recommendations.csv', 'rb') as csvfile:
            recommendations = csv.reader(csvfile, delimiter=',')
            for row in recommendations:

                hazardcategory = DBSession.query(HazardCategory) \
                    .join(HazardLevel) \
                    .join(HazardType) \
                    .filter(HazardLevel.mnemonic == row[1]) \
                    .filter(HazardType.mnemonic == row[0]) \
                    .one()
                hazardcategory.general_recommendation = row[2]
                DBSession.add(hazardcategory)

        categories = []
        for type in [u'EQ', u'FL', u'CY', u'TS', u'CF', u'VA', u'DG']:
            for level in [u'HIG', u'MED', u'LOW', u'VLO']:
                hazardcategory = DBSession.query(HazardCategory) \
                    .join(HazardLevel) \
                    .join(HazardType) \
                    .filter(HazardLevel.mnemonic == level) \
                    .filter(HazardType.mnemonic == type) \
                    .one()
                categories.append(hazardcategory)

        # Then technical recommendations

        hctra = HazardCategoryTechnicalRecommendationAssociation

        with open('data/technical_recommendations.csv', 'rb') as csvfile:
            recommendations = csv.reader(csvfile, delimiter=',')
            next(recommendations, None)  # skip the headers
            for row in recommendations:
                technical_rec = TechnicalRecommendation(**{
                    'text': row[0]
                })
                associations = technical_rec.hazardcategory_associations

                # the other columns are hazard category (type / level)
                for col_index in range(1, 28):
                    value = row[col_index]
                    if value is not '' and value is not 'Y':
                        association = hctra(order=value)
                        association.hazardcategory = categories[col_index - 1]
                        associations.append(association)
                DBSession.add(technical_rec)

        # Climate change recommendations

        DBSession.query(ClimateChangeRecommendation).delete()

        # hazard types and corresponding columns
        hazard_types = [
            (u'FL', 6),
            (u'EQ', 7),
            (u'CY', 8),
            (u'CF', 9),
            (u'DG', 10),
            (u'TS', 11),
            (u'VA', 12),
            (u'LS', 13),
        ]

        with open('data/climate_change_recommendations.csv', 'rb') as csvfile:
            countries = csv.reader(csvfile, delimiter=',')
            next(countries, None)  # skip the headers
            for row in countries:
                division = DBSession.query(AdministrativeDivision) \
                    .filter(AdministrativeDivision.code == row[1]) \
                    .one_or_none()

                if not division:
                    continue
                for hazard_type, column in hazard_types:
                    text = row[column]
                    if text == 'NA':
                        continue

                    climate_rec = ClimateChangeRecommendation()
                    climate_rec.text = row[column]
                    climate_rec.administrativedivision = division
                    climate_rec.hazardtype = DBSession.query(HazardType) \
                        .filter(HazardType.mnemonic == hazard_type).one()
                    DBSession.add(climate_rec)
