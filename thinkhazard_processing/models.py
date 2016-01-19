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

import os
from sqlalchemy import (
    Column,
    ForeignKey,
    Boolean,
    Date,
    Integer,
    String,
    )
from sqlalchemy.orm import relationship

from thinkhazard_common.models import (
    DBSession,
    Base,
    HazardLevel,
    )

from . import settings


class HazardSet(Base):
    __tablename__ = 'hazardset'
    __table_args__ = {u'schema': 'processing'}

    # id is the string id common to the 3 layers,
    # as reported by geonode ("hazard_set" field), eg: "EQ-PA"
    id = Column(String, primary_key=True)

    # a hazardset is related to a hazard type:
    hazardtype_id = Column(Integer,
                           ForeignKey('datamart.enum_hazardtype.id'),
                           nullable=False)

    # "local" is set to false when bounds = -180/-90/180/90
    # this value comes from the linked layers
    local = Column(Boolean)
    # date the data was last updated (defaults to created):
    # this value comes from the linked layers
    data_lastupdated_date = Column(Date, nullable=False)
    # date the metadata was last updated (defaults to created):
    # this value comes from the linked layers
    metadata_lastupdated_date = Column(Date, nullable=False)
    # quality rating for the hazard calculation method
    # ranges from 0 (bad) to 10 (excellent).
    # this value comes from the linked layers
    calculation_method_quality = Column(Integer)
    # quality rating for the study
    # ranges from 0 (bad) to 2 (excellent)
    # this value comes from the linked layers
    scientific_quality = Column(Integer)

    # processing steps:
    # a hazardset starts incomplete.
    # then it becomes complete, which means:
    #   * all layers have been downloaded
    #   * the date, quality, etc fields of the hazardset has been updated
    complete = Column(Boolean, nullable=False, default=False)
    # finally it is processed:
    processed = Column(Boolean, nullable=False, default=False)

    hazardtype = relationship('HazardType', backref="hazardsets")

    def path(self):
        return os.path.join(settings['data_path'],
                            'hazardsets',
                            self.id)

    def layerByLevel(self, level):
        hazardlevel = HazardLevel.get(level)
        return DBSession.query(Layer) \
            .filter(Layer.hazardset_id == self.id) \
            .filter(Layer.hazardlevel_id == hazardlevel.id) \
            .one_or_none()


class Layer(Base):
    __tablename__ = 'layer'
    __table_args__ = {u'schema': 'processing'}

    # the layer is referenced in geonode with an id:
    geonode_id = Column(Integer, primary_key=True)

    # a layer is identified by it's return_period and hazard_set:
    hazardset_id = Column(String, ForeignKey('processing.hazardset.id'),
                          nullable=False)
    # the related hazard_level, inferred from return_period
    hazardlevel_id = Column(Integer,
                            ForeignKey('datamart.enum_hazardlevel.id'))
    # the return period is typically 100, 475, 2475 years but it can vary
    return_period = Column(Integer)

    # Flood hazardtype requires a mask layer
    mask = Column(Boolean, nullable=False)

    # pixel values have a unit:
    hazardunit = Column(String)

    # date the data was last updated (defaults to created):
    data_lastupdated_date = Column(Date, nullable=False)
    # date the metadata was last updated (defaults to created):
    metadata_lastupdated_date = Column(Date, nullable=False)

    # the data can be downloaded at this URL:
    download_url = Column(String, nullable=False)

    # quality rating for the hazard calculation method
    # ranges from 0 (bad) to 10 (excellent)
    calculation_method_quality = Column(Integer, nullable=False)
    # quality rating for the study
    # ranges from 0 (bad) to 2 (excellent)
    scientific_quality = Column(Integer, nullable=False)

    # "local" is set to false when bounds = -180/-90/180/90
    # true otherwise
    local = Column(Boolean, nullable=False)

    # "downloaded" is set to true
    # when the geotiff file has been downloaded
    downloaded = Column(Boolean, nullable=False, default=False)

    hazardset = relationship('HazardSet', backref='layers')
    hazardlevel = relationship('HazardLevel')

    def name(self):
        if self.return_period is None:
            if self.mask:
                return '{}-MASK'.format(self.hazardset_id)
            return self.hazardset_id
        else:
            return '{}-{}'.format(self.hazardset_id, self.return_period)

    def path(self):
        return os.path.join(settings['data_path'],
                            'hazardsets',
                            self.hazardset_id,
                            '{}.tif'.format(self.return_period))


class Output(Base):
    __tablename__ = 'output'
    __table_args__ = {u'schema': 'processing'}
    # processing results are identified by:
    #  * the hazardset they come from
    #  * the administrative division that they qualify
    hazardset_id = Column(String,
                          ForeignKey('processing.hazardset.id'),
                          primary_key=True)
    admin_id = Column(Integer,
                      ForeignKey('datamart.administrativedivision.id'),
                      primary_key=True)
    # the coverage_ratio ranges from 0 to 100
    # it represents the percentage of the admin division area
    # covered by the data in the hazardset
    # (NO-DATA values are not taken into account here)
    coverage_ratio = Column(Integer, nullable=False)
    # hazard_level_id is the processing result
    hazardlevel_id = Column(Integer,
                            ForeignKey('datamart.enum_hazardlevel.id'),
                            nullable=False)

    hazardset = relationship('HazardSet')
    administrativedivision = relationship('AdministrativeDivision')
    hazardlevel = relationship('HazardLevel')
