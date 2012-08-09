from velruse.testing import unittest

class TestProviderSettings(unittest.TestCase):

    def _makeOne(self, settings, prefix=''):
        from velruse.settings import ProviderSettings
        return ProviderSettings(settings, prefix=prefix)

    def test_it(self):
        p = self._makeOne({'v.foo': 'bar'}, 'v.')
        p.update('foo')
        self.assertEqual(p.kwargs, {'foo': 'bar'})
        p.update('foo', dst='baz')
        self.assertEqual(p.kwargs, {'foo': 'bar', 'baz': 'bar'})
        self.assertRaises(KeyError, p.update, 'missing', required=True)
        p.update('missing')
        self.assertEqual(p.kwargs, {'foo': 'bar', 'baz': 'bar'})

    def test_bool(self):
        p = self._makeOne({'is_true': 'true', 'is_false': 'false'})
        p.update('is_true')
        p.update('is_false')
        self.assertEqual(p.kwargs, {'is_true': True, 'is_false': False})
