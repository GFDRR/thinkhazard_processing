import logging
import traceback
import transaction
import datetime
import rasterio
from rasterio import (
    features,
    )
from shapely.geometry import box
from geoalchemy2.shape import to_shape
from sqlalchemy import func

from thinkhazard_common.models import (
    DBSession,
    AdministrativeDivision,
    AdminLevelType,
    HazardLevel,
    )
from .models import (
    HazardSet,
    Layer,
    Output,
    )
from . import settings


logger = logging.getLogger(__name__)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

logger.setLevel(logging.DEBUG)


class ProcessException(Exception):
    def __init__(self, message):
        self.message = message


def process(hazardset_id=None, force=False, dry_run=False):
    ids = DBSession.query(HazardSet.id) \
        .filter(HazardSet.complete.is_(True))
    if hazardset_id is not None:
        ids = ids.filter(HazardSet.id == hazardset_id)
    if not force:
        ids = ids.filter(HazardSet.processed.is_(False))
    if ids.count() == 0:
        logger.info('No hazardset to process')
        return
    for id in ids:
        logger.info(id[0])
        try:
            process_hazardset(id[0], force=force)
            if dry_run:
                logger.info('  Abording transaction')
                transaction.abort()
            else:
                logger.info('  Committing transaction')
                transaction.commit()
        except Exception:
            transaction.abort()
            logger.error(traceback.format_exc())


def process_hazardset(hazardset_id, force=False):
    hazardset = DBSession.query(HazardSet).get(hazardset_id)
    if hazardset is None:
        raise ProcessException('Hazardset {} does not exist.'
                               .format(hazardset_id))

    chrono = datetime.datetime.now()

    if hazardset.processed:
        if force:
            hazardset.processed = False
        else:
            raise ProcessException('Hazardset {} has already been processed.'
                                   .format(hazardset.id))

    logger.info("  Cleaning previous outputs")
    DBSession.query(Output) \
        .filter(Output.hazardset_id == hazardset.id) \
        .delete()
    DBSession.flush()

    type_settings = settings['hazard_types'][hazardset.hazardtype.mnemonic]

    with rasterio.drivers():
        try:
            logger.info("  Opening raster files")
            # Open rasters
            layers = {}
            readers = {}
            if 'values' in type_settings.keys():
                # preprocessed layer
                layer = DBSession.query(Layer) \
                    .filter(Layer.hazardset_id == hazardset.id) \
                    .one()
                reader = rasterio.open(layer.path())

                layers[0] = layer
                readers[0] = reader

            else:
                for level in (u'HIG', u'MED', u'LOW'):
                    hazardlevel = HazardLevel.get(level)
                    layer = DBSession.query(Layer) \
                        .filter(Layer.hazardset_id == hazardset.id) \
                        .filter(Layer.hazardlevel_id == hazardlevel.id) \
                        .one()
                    reader = rasterio.open(layer.path())

                    layers[level] = layer
                    readers[level] = reader
                if ('mask_return_period' in type_settings):
                    layer = DBSession.query(Layer) \
                        .filter(Layer.hazardset_id == hazardset.id) \
                        .filter(Layer.mask.is_(True)) \
                        .one()
                    reader = rasterio.open(layer.path())
                    layers['mask'] = layer
                    readers['mask'] = reader

            outputs = create_outputs(hazardset, layers, readers)
            if outputs:
                DBSession.add_all(outputs)

        finally:
            logger.info("  Closing raster files")
            for key, reader in readers.iteritems():
                if reader and not reader.closed:
                    reader.close()

    hazardset.processed = True
    DBSession.flush()

    logger.info('  Successfully processed {}, {} outputs generated in {}'
                .format(hazardset.id,
                        len(outputs),
                        datetime.datetime.now() - chrono))

    return True


def create_outputs(hazardset, layers, readers):
    type_settings = settings['hazard_types'][hazardset.hazardtype.mnemonic]
    adminlevel_REG = AdminLevelType.get(u'REG')

    bbox = None
    for reader in readers.itervalues():
        polygon = polygon_from_boundingbox(reader.bounds)
        if bbox is None:
            bbox = polygon
        else:
            bbox = bbox.intersection(polygon)

    admindivs = DBSession.query(AdministrativeDivision) \
        .filter(AdministrativeDivision.leveltype_id == adminlevel_REG.id) \
        .filter(func.ST_Intersects(AdministrativeDivision.geom,
                func.ST_GeomFromText(bbox.wkt, 4326))) \
        .order_by(AdministrativeDivision.id)  # Needed for windowed querying

    current = 0
    last_percent = 0
    outputs = []
    total = admindivs.count()
    logger.info('  Iterating over {} administrative divisions'.format(total))

    # Windowed querying to limit memory usage
    limit = 1000  # 1000 records <=> 10 Mo
    admindivs = admindivs.limit(limit)
    for offset in xrange(0, total, limit):
        admindivs = admindivs.offset(offset)

        for admindiv in admindivs:
            current += 1

            if admindiv.geom is None:
                logger.warning('    {}-{} has null geometry'
                               .format(admindiv.code, admindiv.name))
                continue

            shape = to_shape(admindiv.geom)

            # Try block to include admindiv.code in exception message
            try:
                if 'values' in type_settings.keys():
                    # preprocessed layer
                    hazardlevel = preprocessed_hazardlevel(
                        type_settings,
                        layers[0], readers[0],
                        shape)
                else:
                    hazardlevel = notpreprocessed_hazardlevel(
                        hazardset.hazardtype.mnemonic, type_settings, layers,
                        readers, shape)

            except Exception as e:
                e.message = ("{}-{} raises an exception :\n{}"
                             .format(admindiv.code, admindiv.name, e.message))
                raise

            # Create output record
            if hazardlevel is not None:
                output = Output()
                output.hazardset = hazardset
                output.admin_id = admindiv.id
                output.hazardlevel = hazardlevel
                # TODO: calculate coverage ratio
                output.coverage_ratio = 100
                outputs.append(output)

            # Remove admindiv from memory
            DBSession.expunge(admindiv)

            percent = int(100.0 * current / total)
            if percent % 10 == 0 and percent != last_percent:
                logger.info('  ... processed {}%'.format(percent))
                last_percent = percent

    return outputs


def preprocessed_hazardlevel(type_settings, layer, reader, geometry):
    hazardlevel = None

    for polygon in geometry.geoms:
        window = reader.window(*polygon.bounds)
        data = reader.read(1, window=window, masked=True)

        if data.shape[0] * data.shape[1] == 0:
            continue
        if data.mask.all():
            continue

        mask = features.geometry_mask(
            [polygon],
            out_shape=data.shape,
            transform=reader.window_transform(window),
            all_touched=True)

        data.mask = data.mask | mask

        if data.mask.all():
            continue

        for level in (u'HIG', u'MED', u'LOW', u'VLO'):
            level_obj = HazardLevel.get(level)
            if level_obj <= hazardlevel:
                break

            if level in type_settings['values']:
                values = type_settings['values'][level]
                for value in values:
                    if value in data:
                        hazardlevel = level_obj
                        break

    return hazardlevel


def notpreprocessed_hazardlevel(hazardtype, type_settings, layers, readers,
                                geometry):
    level_VLO = HazardLevel.get(u'VLO')

    hazardlevel = None

    # Create some optimization caches
    polygons = {}
    bboxes = {}
    masks = {}

    inverted_comparison = ('inverted_comparison' in type_settings and
                           type_settings['inverted_comparison'])

    for level in (u'HIG', u'MED', u'LOW'):
        layer = layers[level]
        reader = readers[level]

        threshold = get_threshold(hazardtype,
                                  layer.local,
                                  layer.hazardlevel.mnemonic,
                                  layer.hazardunit)
        if threshold is None:
            raise ProcessException(
                'No threshold found for {} {} {} {}'
                .format(hazardtype,
                        'local' if layer.local else 'global',
                        layer.hazardlevel.mnemonic,
                        layer.hazardunit))

        for i in xrange(0, len(geometry.geoms)):
            if level == u'HIG':
                polygon = geometry.geoms[i]
                bbox = polygon.bounds
                polygons[i] = polygon
                bboxes[i] = bbox
            else:
                polygon = polygons[i]
                bbox = bboxes[i]

            window = reader.window(*bbox)
            data = reader.read(1, window=window, masked=True)

            if data.shape[0] * data.shape[1] == 0:
                continue
            if data.mask.all():
                continue

            if inverted_comparison:
                data = data < threshold
            else:
                data = data > threshold

            if ('mask_return_period' in type_settings):
                mask = readers['mask'].read(1, window=window, masked=True)
                if inverted_comparison:
                    mask = mask < threshold
                else:
                    mask = mask > threshold

                data.mask = data.mask | mask

            if level == u'HIG':
                mask = features.geometry_mask(
                    [polygon],
                    out_shape=data.shape,
                    transform=reader.window_transform(window),
                    all_touched=True)
                masks[i] = mask
            else:
                mask = masks[i]

            data.mask = data.mask | mask

            if data.any():
                hazardlevel = layer.hazardlevel
                break  # No need to go further

            if data.mask.all():
                continue

            if hazardlevel is None:
                hazardlevel = level_VLO

        if hazardlevel == layer.hazardlevel:
            break  # No need to go further

    return hazardlevel


def polygon_from_boundingbox(boundingbox):
    return box(boundingbox[0],
               boundingbox[1],
               boundingbox[2],
               boundingbox[3])


def get_threshold(hazardtype, local, level, unit):
    mysettings = settings['hazard_types'][hazardtype]['thresholds']
    while type(mysettings) is dict:
        if 'local' in mysettings.keys():
            mysettings = mysettings['local'] if local else mysettings['global']
        elif 'HIG' in mysettings.keys():
            mysettings = mysettings[level]
        elif unit in mysettings.keys():
            mysettings = mysettings[unit]
    return float(mysettings)
