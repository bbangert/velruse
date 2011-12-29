import unittest2 as unittest


class TestBaseEncoding(unittest.TestCase):

    def test_encode(self):
        from velruse.baseconvert import base_encode
        self.assertEqual(base_encode(42), 'L')
        self.assertEqual(base_encode(425242), '4rBC')
        self.assertEqual(base_encode(0), '2')

    def test_bad_encode(self):
        from velruse.baseconvert import base_encode
        self.assertRaises(TypeError, base_encode, 'fred')

    def test_decode(self):
        from velruse.baseconvert import base_decode
        self.assertEqual(base_decode('L'), 42)
        self.assertEqual(base_decode('4rBC'), 425242)
        self.assertEqual(base_decode('2'), 0)

    def test_bad_decode(self):
        from velruse.baseconvert import base_decode
        self.assertRaises(ValueError, base_decode, '381')
