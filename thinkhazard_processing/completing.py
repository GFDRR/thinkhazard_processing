import logging
import transaction
from sqlalchemy import func

from thinkhazard_common.models import (
    DBSession,
    HazardSet,
    Layer,
    )

from . import settings


logger = logging.getLogger(__name__)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

logger.setLevel(logging.DEBUG)


def clearall():
    logger.info('Reset all hazardsets to incomplete state')
    DBSession.query(HazardSet).update({
        HazardSet.processed: False
    })
    DBSession.flush()


def complete(hazardset_id=None, force=False, dry_run=False):
    if force:
        try:
            clearall()
            if dry_run:
                transaction.abort()
            else:
                transaction.commit()
        except:
            transaction.abort()
            raise

    ids = DBSession.query(HazardSet.id)
    if not force:
        ids = ids.filter(HazardSet.complete.is_(False))
    if hazardset_id is not None:
        ids = ids.filter(HazardSet.id == hazardset_id)
    for id in ids:
        logger.info('  Working on hazardset {}'.format(id[0]))
        try:
            if not complete_hazardset(id[0]):
                hazardset = DBSession.query(HazardSet).get(id)
                if hazardset.processed:
                    logger.info('Deleting {} previous outputs related \
                                to this hazardset'.format(
                                hazardset.outputs.count()))
                    hazardset.outputs.delete()
            if dry_run:
                transaction.abort()
            else:
                transaction.commit()
        except Exception as e:
            transaction.abort()
            logger.error(e.message)


def complete_hazardset(hazardset_id, dry_run=False):
    hazardset = DBSession.query(HazardSet).get(hazardset_id)
    if hazardset is None:
        raise Exception('Hazardset {} does not exist.'
                        .format(hazardset_id))

    hazardtype = hazardset.hazardtype
    type_settings = settings['hazard_types'][hazardtype.mnemonic]
    preprocessed = 'values' in type_settings

    layers = []
    if preprocessed:
        if len(hazardset.layers) == 0:
            logger.info('  No layer found')
            return False
        layers.append(hazardset.layers[0])
    else:
        for level in (u'LOW', u'MED', u'HIG'):
            layer = hazardset.layerByLevel(level)
            if layer is None:
                logger.info('  No layer for level {}'.format(level))
                return False
            layers.append(layer)
        if ('mask_return_period' in type_settings):
            layer = DBSession.query(Layer) \
                .filter(Layer.hazardset_id == hazardset_id) \
                .filter(Layer.mask.is_(True))
            if layer.count() == 0:
                logger.info('  No mask layer')
                return False
            layers.append(layer.one())

    for layer in layers:
        if not layer.downloaded:
            logger.info('  No data for layer {}'.format(layer.name()))
            return False

    stats = DBSession.query(
        Layer.local,
        func.min(Layer.data_lastupdated_date),
        func.min(Layer.metadata_lastupdated_date),
        func.min(Layer.calculation_method_quality),
        func.min(Layer.scientific_quality)) \
        .filter(Layer.hazardset_id == hazardset.id) \
        .group_by(Layer.local)

    if stats.count() > 1:
        logger.warning('  Mixed local and global layers')
        return False

    stat = stats.one()

    hazardset.local = stat[0]
    hazardset.data_lastupdated_date = stat[1]
    hazardset.metadata_lastupdated_date = stat[2]
    hazardset.calculation_method_quality = stat[3]
    hazardset.scientific_quality = stat[4]
    hazardset.complete = True
    DBSession.flush()

    logger.info('  Completed')
    return True
