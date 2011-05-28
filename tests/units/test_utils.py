from nose.tools import eq_, assert_true, raises

from velruse.utils import load_package_obj

class TestLoadPackageObj(object):
    
    def test_ok(self):
        from velruse.store.memstore import MemoryStore
        loaded = load_package_obj('velruse.store.memstore:MemoryStore')
        assert_true(loaded is MemoryStore)
    
    @raises(AttributeError)
    def test_member_not_there(self):
        load_package_obj('velruse.store.memstore:BadMember')

    @raises(ImportError)
    def test_module_not_there(self):
        load_package_obj('velruse.badmodule:BadMember')
        
    def test_bad_format(self):
        try:
            load_package_obj('MemStore')
        except ValueError,e:
            eq_(e.args[0],
                "Could not parse package and object name "
                "from 'MemStore', should be 'package:object'")
        else:
            raise AssertionError('No exception raised!')
