from velruse.utils import splitlines

def includeme(config):
    registry = config.registry
    settings = registry.settings
    autoload = settings.get('velruse.providers', '')
    registry.velruse_autoload = splitlines(autoload)

    config.include('velruse.providers.bitbucket')
    config.include('velruse.providers.douban')
    config.include('velruse.providers.facebook')
    config.include('velruse.providers.github')
    config.include('velruse.providers.google')
    config.include('velruse.providers.lastfm')
    config.include('velruse.providers.linkedin')
    config.include('velruse.providers.live')
    config.include('velruse.providers.openid')
    config.include('velruse.providers.qq')
    config.include('velruse.providers.renren')
    config.include('velruse.providers.taobao')
    config.include('velruse.providers.twitter')
    config.include('velruse.providers.weibo')
    config.include('velruse.providers.yahoo')
