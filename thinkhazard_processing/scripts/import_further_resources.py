'''
This script was created to manually add further resources. It should be deleted
once we get documents extracted from geonode.
'''
import sys
import transaction

from sqlalchemy import engine_from_config

from thinkhazard_common.models import (
    DBSession,
    HazardType,
    HazardCategory,
    FurtherResource,
    HazardCategoryFurtherResourceAssociation,
    )

from .. import settings


def import_further_resources():
    with transaction.manager:

        DBSession.query(HazardCategoryFurtherResourceAssociation).delete()
        DBSession.query(FurtherResource).delete()
        DBSession.flush()

        # Earthquake
        further_resources = [
            FurtherResource(**{
                'text': u'Educational web resources on earthquakes and seismic hazard',  # NOQA
                'url': u'http://earthquake.usgs.gov/learn/?source=sitemap'
            }),
            FurtherResource(**{
                'text': u'Publications by the Global Facility for Disaster Reduction and Recovery',  # NOQA
                'url': u'https://www.gfdrr.org/publications'
            }),
        ]

        add_resources(u'EQ', further_resources)

        # Flood
        further_resources = [
            FurtherResource(**{
                'text': u'The Aqueduct Global Flood Analyzer. Note that this tool only provides information about river flooding (not coastal, pluvial or flash flooding)',  # NOQA
                'url': u'http://www.wri.org/floods'
            }),
            FurtherResource(**{
                'text': u'The Climate app, providing information on possible risk reducing intervention measures under site-specific conditions',  # NOQA
                'url': u'http://www.climateapp.nl/'
            }),
            FurtherResource(**{
                'text': u'Publications by GFDRR, providing information on disaster risk assessment, risk reduction and preparedness',  # NOQA
                'url': u'https://www.gfdrr.org/publications'
            }),
            FurtherResource(**{
                'text': u'RIMAROCC, providing a risk management framework for road managers and operators dealing with climate change',  # NOQA
                'url': u'http://www.cedr.fr/home/index.php?id=251&dlpath=2008%20Call%20Road%20Owners%20Getting%20to%20Grips%20with%20Climate%20Change%2FRIMAROCC&cHash=0d3ce2ac10a4d935d9012c515d8e1dc3'  # NOQA
            }),
            FurtherResource(**{
                'text': u'FLOOD PROBE, research on technologies for the cost-effective flood protection of the built environment',  # NOQA
                'url': u'http://www.floodprobe.eu'
            }),
        ]

        add_resources(u'FL', further_resources)


def add_resources(hazard_type, resources):
    for resource in resources:
        categories = DBSession.query(HazardCategory) \
            .join(HazardType) \
            .filter(HazardType.mnemonic == hazard_type)
        for category in categories:
            association = HazardCategoryFurtherResourceAssociation(order=1)
            association.hazardcategory = category
            resource.hazardcategory_associations.append(association)
        DBSession.add(resource)


def main(argv=sys.argv):
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)

    import_further_resources()
