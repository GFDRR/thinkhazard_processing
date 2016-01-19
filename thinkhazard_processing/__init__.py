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
#

import os
import yaml


def load_settings():
    root_folder = os.path.join(os.path.dirname(__file__), '..')
    main_settings_path = os.path.join(root_folder,
                                      'thinkhazard_processing.yaml')
    with open(main_settings_path, 'r') as f:
        settings = yaml.load(f.read())

    local_settings_path = os.path.join(root_folder,
                                       'local_settings.yaml')
    if os.path.exists(local_settings_path):
        with open(local_settings_path, 'r') as f:
            settings.update(yaml.load(f.read()))

    return settings

settings = load_settings()
