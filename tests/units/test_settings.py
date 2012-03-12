import unittest2 as unittest

class TestProviderSettings(unittest.TestCase):

    def _makeOne(self, settings, prefix):
        from velruse.utils import ProviderSettings
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
