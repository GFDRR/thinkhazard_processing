import yaml
from sqlalchemy import engine_from_config
from .. import settings
from ..scripts.initializedb import initdb_processing


local_settings_path = 'local.tests.yaml'

with open(local_settings_path, 'r') as f:
    settings.update(yaml.load(f.read()))


def initdb():
    engine = engine_from_config(settings, 'sqlalchemy.')
    initdb_processing(engine, True)

initdb()
