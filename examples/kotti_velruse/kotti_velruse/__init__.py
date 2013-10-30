from pyramid.i18n import TranslationStringFactory


log = __import__('logging').getLogger(__name__)


_ = TranslationStringFactory('kotti_velruse')


def kotti_configure(settings):
    settings['pyramid.includes'] += ' velruse.app'
    settings['pyramid.includes'] += ' kotti_velruse.views'
