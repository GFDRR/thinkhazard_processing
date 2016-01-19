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
# Author: François Van Der Biest <francois.vanderbiest@camptocamp.com>
#

import logging
import os
from urlparse import urlunsplit
from httplib2 import Http
import transaction

from thinkhazard_common.models import DBSession

from . import settings
from .models import Layer


logger = logging.getLogger(__name__)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

logger.setLevel(logging.DEBUG)


geonode = settings['geonode']


def clearall():
    logger.info('Reset all layer to not downloaded state.')
    DBSession.query(Layer).update({
        Layer.downloaded: False
    })
    DBSession.flush()


def download(title=None, force=False, dry_run=False):
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

    geonode_ids = DBSession.query(Layer.geonode_id)

    if not force:
        geonode_ids = geonode_ids.filter(Layer.downloaded.is_(False))

    if title is not None:
        geonode_ids = geonode_ids.filter(Layer.title == title)

    for geonode_id in geonode_ids:
        try:
            download_layer(geonode_id)
            if dry_run:
                transaction.abort()
            else:
                transaction.commit()
        except Exception as e:
            transaction.abort()
            logger.error('{} raise an exception :\n{}'
                         .format(geonode_id, e.message))


def download_layer(geonode_id):
    layer = DBSession.query(Layer).get(geonode_id)
    if layer is None:
        raise Exception('Layer {} does not exist.'.format(geonode_id))

    logger.info('Downloading layer {}'.format(layer.name()))

    dir_path = os.path.dirname(layer.path())
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    if not os.path.isfile(layer.path()):
        h = Http()
        url = urlunsplit((geonode['scheme'],
                          geonode['netloc'],
                          layer.download_url,
                          '',
                          ''))
        logger.info('Retrieving {}'.format(url))
        response, content = h.request(url)

        try:
            with open(layer.path(), 'wb') as f:
                f.write(content)
                layer.downloaded = True
        except EnvironmentError:
            logger.error('Writing data from layer {} failed'.format(
                layer.name()))

    DBSession.flush()
