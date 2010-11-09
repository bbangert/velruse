"""In Memory UserStore implementation"""
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.sql import select, delete
from sqlalchemy.ext.declarative import declarative_base, Column
from sqlalchemy import String, Text, DateTime
from velruse.store.interface import UserStore
try:
    import simplejson as json
except ImportError:
    import json


SQLBase = declarative_base()


class KeyStorage(SQLBase):
    __tablename__ = 'velruse_key_storage'
    key = Column(String(200), primary_key=True, nullable=False)
    value = Column(Text(), nullable=False)
    expires = Column(DateTime())


class SQLStore(UserStore):
    """Memory Storage for Auth Provider"""
    def __init__(self, sqluri, pool_size=100, pool_recycle=3600,
                 logging_name='velruse', reset_on_return=True):
        self.sqluri = sqluri
        kw = dict(pool_size=int(pool_size),
                  pool_recycle=int(pool_recycle),
                  logging_name=logging_name)

        if self.sqluri.startswith('mysql'):
            kw['reset_on_return'] = reset_on_return

        self.engine = create_engine(sqluri, **kw)
        ## FIXME: not threadsafe:
        KeyStorage.metadata.bind = self.engine

    def create(self):
        KeyStorage.__table__.create(checkfirst=True)

    @classmethod
    def load_from_config(cls, config):
        ## FIXME: load other vars
        kw = {
            'sqluri': config['DB'],
            }
        for key in ['pool_size', 'pool_recycle', 'logging_name',
                    'reset_on_return']:
            ## FIXME: type coercion?
            if key in config:
                kw[key] = config[key]
        return cls(**kw)

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
            delete(KeyStorage,
                   KeyStorage.__table__.c.key == key))
        ## FIXME: do I need to tell if I was successful?
        return True

    def purge_expired(self):
        self.engine.execute(
            delete(KeyStorage,
                   KeyStorage.__table__.c.expires < datetime.now()))
        return True
