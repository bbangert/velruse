from pyramid.config import Configurator
from pyramid.session import UnencryptedCookieSessionFactoryConfig

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    session_factory = UnencryptedCookieSessionFactoryConfig(
        settings['cookie.secret'],
    )
    config = Configurator(
        settings=settings,
        session_factory=session_factory,
    )
    config.include('velruse')

    config.add_facebook_login(
        settings['velruse.facebook.app_id'],
        settings['velruse.facebook.app_secret'])

#    config.add_github_login(
#        settings['velruse.github.app_id'],
#        settings['velruse.github.app_secret'])

#    config.add_twitter_login(
#        settings['velruse.twitter.app_id'],
#        settings['velruse.twitter.app_secret'])

    config.scan('.views')
    return config.make_wsgi_app()
