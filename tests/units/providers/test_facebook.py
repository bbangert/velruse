import unittest

import mock
import pyramid.testing

class TestIncludeMe(unittest.TestCase):
    def test_it(self):
        from velruse.providers.facebook import includeme
        config = mock.Mock()
        config.registry.settings = {
            'velruse.facebook.app_id': 'id',
            'velruse.facebook.app_secret': 'secret',
            'velruse.facebook.scope': 'scope',
        }
        includeme(config)
        self.assertEqual(config.add_route.call_count, 2)
        self.assertEqual(config.add_route.call_args_list[0],
                         (('facebook_login', '/facebook/login'), {}))
        self.assertEqual(config.add_route.call_args_list[1][0],
                         ('facebook_process', '/facebook/process'))
        self.assertEqual(
            config.add_route.call_args_list[1][1]['use_global_views'], True)
        self.assertTrue(config.add_route.call_args_list[1][1]['factory'])
        self.assertEqual(config.add_view.call_count, 1)
        self.assertEqual(config.add_view.call_args[1]['route_name'],
                         'facebook_login')

    def test_it_noscope(self):
        from velruse.providers.facebook import includeme
        config = mock.Mock()
        config.registry.settings = {
            'velruse.facebook.app_id': 'id',
            'velruse.facebook.app_secret': 'secret',
        }
        includeme(config)
        self.assertEqual(config.add_route.call_count, 2)
        self.assertEqual(config.add_route.call_args_list[0],
                         (('facebook_login', '/facebook/login'), {}))
        self.assertEqual(config.add_route.call_args_list[1][0],
                         ('facebook_process', '/facebook/process'))
        self.assertEqual(
            config.add_route.call_args_list[1][1]['use_global_views'], True)
        self.assertTrue(config.add_route.call_args_list[1][1]['factory'])
        self.assertEqual(config.add_view.call_count, 1)
        self.assertEqual(config.add_view.call_args[1]['route_name'],
                         'facebook_login')


class TestFacebookProvider(unittest.TestCase):
    def setUp(self):
        self.config = config = pyramid.testing.setUp()
        config.add_route('facebook_login', '/facebook/login')
        config.add_route('facebook_process', '/facebook/process')

    def makeOne(self, app_id, app_secret, scope=None):
        from velruse.providers.facebook import FacebookProvider
        provider = FacebookProvider(app_id, app_secret, scope=scope)
        return provider

    def makeResponse(self, status_code, content):
        resp = mock.Mock()
        resp.status_code = status_code
        resp.content = content
        return resp

    def test_login_with_scope(self):
        provider = self.makeOne('id', 'secret')
        url = mock.Mock(return_value='http://example.com/cb')
        provider.oauth_url = url
        request = DummyRequest(post={'scope': 'email'})
        request.application_url = 'http://example.com'
        resp = provider.login(request)
        self.assertEqual(resp.status_int, 302)
        self.assertEqual(resp.headers['location'], 'http://example.com/cb')
        self.assertEqual(url.call_count, 1)
        self.assertEqual(url.call_args[1]['scope'], 'email')
        self.assertEqual(url.call_args[1]['redirect_uri'],
                         'http://example.com/facebook/process')

    def test_login_with_default_scope(self):
        provider = self.makeOne('id', 'secret', scope='username')
        url = mock.Mock(return_value='http://example.com/cb')
        provider.oauth_url = url
        request = DummyRequest(post={'scope': 'email'})
        request.application_url = 'http://example.com'
        resp = provider.login(request)
        self.assertEqual(resp.status_int, 302)
        self.assertEqual(resp.headers['location'], 'http://example.com/cb')
        self.assertEqual(url.call_count, 1)
        self.assertEqual(url.call_args[1]['scope'], 'username')
        self.assertEqual(url.call_args[1]['redirect_uri'],
                         'http://example.com/facebook/process')

    def test_login_with_no_scope(self):
        provider = self.makeOne('id', 'secret')
        url = mock.Mock(return_value='http://example.com/cb')
        provider.oauth_url = url
        request = DummyRequest(method='POST')
        request.application_url = 'http://example.com'
        resp = provider.login(request)
        self.assertEqual(resp.status_int, 302)
        self.assertEqual(resp.headers['location'], 'http://example.com/cb')
        self.assertEqual(url.call_count, 1)
        self.assertEqual(url.call_args[1]['scope'], '')
        self.assertEqual(url.call_args[1]['redirect_uri'],
                         'http://example.com/facebook/process')

    def test_oauth_url(self):
        from urlparse import urlsplit, parse_qs
        provider = self.makeOne('id', 'secret')
        url = provider.oauth_url(
            scope='email', state='5', redirect_uri='http://example.com/cb')
        parts = urlsplit(url)
        self.assertEqual(parts.netloc, 'www.facebook.com')
        self.assertEqual(parts.path, '/dialog/oauth/')
        qs = parse_qs(parts.query)
        self.assertEqual(qs['client_id'], ['id'])
        self.assertEqual(qs['state'], ['5'])
        self.assertEqual(qs['redirect_uri'], ['http://example.com/cb'])
        self.assertEqual(qs['scope'], ['email'])

    def test_access_url(self):
        from urlparse import urlsplit, parse_qs
        provider = self.makeOne('id', 'secret')
        url = provider.access_url(
            redirect_uri='http://example.com/cb', code='101')
        parts = urlsplit(url)
        self.assertEqual(parts.netloc, 'graph.facebook.com')
        self.assertEqual(parts.path, '/oauth/access_token')
        qs = parse_qs(parts.query)
        self.assertEqual(qs['client_id'], ['id'])
        self.assertEqual(qs['client_secret'], ['secret'])
        self.assertEqual(qs['code'], ['101'])
        self.assertEqual(qs['redirect_uri'], ['http://example.com/cb'])

    def test_graph_url(self):
        from urlparse import urlsplit, parse_qs
        provider = self.makeOne('id', 'secret')
        url = provider.graph_url(access_token='token')
        parts = urlsplit(url)
        self.assertEqual(parts.netloc, 'graph.facebook.com')
        self.assertEqual(parts.path, '/me')
        qs = parse_qs(parts.query)
        self.assertEqual(qs['access_token'], ['token'])

    def test_process_csrf_failure(self):
        from velruse.exceptions import CSRFError
        provider = self.makeOne('id', 'secret')
        request = DummyRequest(params={'state': '5'})
        self.assertRaises(CSRFError, provider.process, request)

    def test_process_csrf_failure2(self):
        from velruse.exceptions import CSRFError
        provider = self.makeOne('id', 'secret')
        request = DummyRequest()
        request.session['state'] = 5
        self.assertRaises(CSRFError, provider.process, request)

    def test_process_no_code(self):
        from velruse.exceptions import AuthenticationDenied
        provider = self.makeOne('id', 'secret')
        request = DummyRequest(params={'state': '5'})
        request.session['state'] = '5'
        resp = provider.process(request)
        self.assertTrue(isinstance(resp, AuthenticationDenied))

    def test_process_bad_access_token_request(self):
        from velruse.exceptions import ThirdPartyFailure
        provider = self.makeOne('id', 'secret')
        requests = mock.Mock()
        requests.get.side_effect = multieffect(
            self.makeResponse(status_code=400, content='content')
        )
        provider.requests = requests
        request = DummyRequest(params={'state': '5', 'code': '101'})
        request.session['state'] = '5'
        self.assertRaises(ThirdPartyFailure, provider.process, request)

    def test_process_bad_graph_request(self):
        from velruse.exceptions import ThirdPartyFailure
        provider = self.makeOne('id', 'secret')
        requests = mock.Mock()
        requests.get.side_effect = multieffect(
            self.makeResponse(status_code=200,
                              content='access_token=token&expires=5108'),
            self.makeResponse(status_code=400, content='failure'),
        )
        provider.requests = requests
        request = DummyRequest(params={'state': '5', 'code': '101'})
        request.session['state'] = '5'
        self.assertRaises(ThirdPartyFailure, provider.process, request)

    def test_process(self):
        provider = self.makeOne('id', 'secret')
        requests = mock.Mock()
        requests.get.side_effect = multieffect(
            self.makeResponse(status_code=200,
                              content='access_token=token&expires=5108'),
            self.makeResponse(status_code=200, content=
'''{
   "id": "1",
   "name": "Homer Simpson",
   "first_name": "Homer",
   "last_name": "Simpson",
   "link": "http://www.facebook.com/homer.simpson",
   "username": "homer.simpson",
   "gender": "male",
   "timezone": -6,
   "locale": "en_US",
   "verified": true,
   "updated_time": "2011-03-22T20:46:34+0000"
}'''),
        )
        provider.requests = requests
        request = DummyRequest(params={'state': '5', 'code': '101'})
        request.session['state'] = '5'
        resp = provider.process(request)
        self.assertEqual(requests.get.call_count, 2)
        self.assertEqual(resp.credentials, {'oauthAccessToken': 'token'})
        self.assertEqual(
            resp.profile,
            {
                'accounts': [{'domain': 'facebook.com', 'userid': '1'}],
                'displayName': 'Homer Simpson',
                'gender': 'male',
                'name': {
                    'familyName': 'Simpson',
                    'formatted': 'Homer Simpson',
                    'givenName': 'Homer',
                },
                'preferredUsername': 'homer.simpson',
            })

DummyRequest = pyramid.testing.DummyRequest

def multieffect(*returns):
    opts = list(returns)
    opts.reverse()
    def side_effect(*args):
        val = opts.pop()
        if isinstance(val, Exception):
            raise val
        return val
    return side_effect
