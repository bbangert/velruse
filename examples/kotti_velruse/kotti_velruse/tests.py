import unittest

from pyramid import testing

import velruse.app


class ViewTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def test_login_view(self):
        from .views import login_view
        request = testing.DummyRequest()
        providers = velruse.app.find_providers(request.registry.settings)
        info = login_view(request)
        self.assertEqual(info['providers'], providers)
