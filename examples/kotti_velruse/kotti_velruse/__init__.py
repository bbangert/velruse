from pyramid.config import Configurator

import velruse.app


log = __import__('logging').getLogger(__name__)


def includeme(config):
    velruse.app.includeme(config)
    config.scan()


def kotti_configure(settings):
    log.info('providers = {}'.format( velruse.app.find_providers(settings) ))
    settings['pyramid.includes'] += ' kotti_velruse.views'


#def main(global_conf, **settings):
#    """ This function returns a Pyramid WSGI application.
#    """
#    config = Configurator(settings=settings)
#
#    config.add_static_view('static', 'static', cache_max_age=3600)
#    config.add_route('home', '/')
#    config.add_route('login', '/login')
#    config.add_route('logged_in', '/logged_in')
#
#    # wires velruse
#    velruse.app.includeme(config)
#
#    config.scan()
#    return config.make_wsgi_app()
