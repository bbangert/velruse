from pyramid.config import Configurator

import velruse.app
import views


log = __import__('logging').getLogger(__name__)


def includeme(config):
    velruse.app.includeme(config)
    views.includeme(config)
