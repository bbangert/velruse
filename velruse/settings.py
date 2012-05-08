def splitlines(s):
    return filter(None, [x.strip() for x in s.splitlines()])


class ProviderSettings(object):
    def __init__(self, settings, prefix=''):
        self.settings = settings
        self.prefix = prefix
        self.kwargs = {}

    def update(self, src, dst=None, required=False):
        if dst is None:
            dst = src
        key = self.prefix + src
        if key in self.settings:
            value = self.settings[key]
            self.kwargs[dst] = value
        elif required:
            raise KeyError('missing required setting "%s"' % key)
