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

    #config.add_facebook_login(
    #    settings['velruse.facebook.app_id'],
    #    settings['velruse.facebook.app_secret'])

    #config.add_douban_login(
    #    settings['velruse.douban.consumer_key'],
    #    settings['velruse.douban.consumer_secret'])

    #config.add_weibo_login(
    #    settings['velruse.weibo.app_id'],
    #    settings['velruse.weibo.app_secret'])

    #config.add_qq_login(
    #    settings['velruse.qq.app_id'],
    #    settings['velruse.qq.app_secret'])

    #config.add_taobao_login(
    #    settings['velruse.taobao.app_id'],
    #    settings['velruse.taobao.app_secret'])

    #config.add_renren_login(
    #    settings['velruse.renren.app_id'],
    #    settings['velruse.renren.app_secret'])

    #config.add_github_login(
    #    settings['velruse.github.app_id'],
    #    settings['velruse.github.app_secret'])

    #config.add_twitter_login(
    #    settings['velruse.twitter.app_id'],
    #    settings['velruse.twitter.app_secret'])

    config.scan('.views')
    return config.make_wsgi_app()
