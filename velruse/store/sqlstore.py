"""In Memory UserStore implementation"""
from datetime import datetime, timedelta
import json

from sqlalchemy import engine_from_config
from sqlalchemy.sql import select, delete
from sqlalchemy.ext.declarative import declarative_base, Column
from sqlalchemy import String, Text, DateTime

from velruse.store.interface import UserStore


SQLBase = declarative_base()


def includeme(config):
    settings = config.registry.settings
    engine = engine_from_config(settings, 'velruse.store.')
    store = SQLStore(engine)
    config.registry.velruse_store = store


class KeyStorage(SQLBase):
    __tablename__ = 'velruse_key_storage'
    key = Column(String(200), primary_key=True, nullable=False)
    value = Column(Text(), nullable=False)
    expires = Column(DateTime())


class SQLStore(UserStore):
    """Memory Storage for Auth Provider"""
    def __init__(self, engine):
        self.engine = engine

    def create(self):
        KeyStorage.__table__.create(checkfirst=True, bind=self.engine)

    def retrieve(self, key):
        s = KeyStorage.__table__
        res = self.engine.execute(select([s.c.value], s.c.key == key))
        res = res.fetchone()
        if res is None:
            return None
        else:
            return json.loads(res[0])

    def store(self, key, value, expires=None):
        if expires:
            expiration = datetime.now() + timedelta(seconds=expires)
        value = json.dumps(value)
        self.engine.execute(
            KeyStorage.__table__.insert(),
            key=key, value=value, expires=expiration)
        return True

    def delete(self, key):
        self.engine.execute(
            delete(KeyStorage.__table__,
                   KeyStorage.__table__.c.key == key))
        ## FIXME: do I need to tell if I was successful?
        return True

    def purge_expired(self):
        self.engine.execute(
            delete(KeyStorage,
                   KeyStorage.__table__.c.expires < datetime.now()))
        return True
