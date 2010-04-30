from nose.tools import eq_, raises

from velruse.baseconvert import base_encode, base_decode

class TestBaseEncoding(object):
    def test_encode(self):
        eq_(base_encode(42), 'L')
        eq_(base_encode(425242), '4rBC')
        eq_(base_encode(0), '2')
    
    @raises(TypeError)
    def test_bad_encode(self):
        base_encode('fred')

    def test_decode(self):
        eq_(base_decode('L'), 42)
        eq_(base_decode('4rBC'), 425242)
        eq_(base_decode('2'), 0)

    @raises(ValueError)
    def test_bad_decode(self):
        base_decode('381')
