import json
import os
import unittest

from nose.plugins.skip import SkipTest

from pyramid.paster import get_app

from selenium import webdriver
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from webtest.http import StopableWSGIServer

from velruse.compat import ConfigParser

config = {}
browser = None  # populated in setUpModule
server = None  # populated in setUpModule

def splitlines(s):
    return filter(None, [c.strip()
                         for x in s.splitlines()
                         for c in x.split(', ')])

def setUpModule():
    global browser, server

    inipath = os.path.abspath(
        os.environ.get('TEST_INI', 'test.ini'))
    if not os.path.isfile(inipath):
        raise RuntimeError(
            'Cannot find INI file to setup selenium tests. '
            'Please specify the path via the TEST_INI environment variable '
            'or by adding a test.ini file to the current directory.')

    parser = ConfigParser()
    parser.read(inipath)

    config.update(parser.items('testconfig'))
    config['test_providers'] = splitlines(config['test_providers'])

    app = get_app(inipath)
    port = int(config['app_port'])
    server = StopableWSGIServer.create(app, port=port)

    driver = config.get('selenium.driver', 'firefox')
    browser = {
        'firefox': webdriver.Firefox,
        'chrome': webdriver.Chrome,
        'ie': webdriver.Ie,
    }[driver]()

def tearDownModule():
    if browser is not None:
        browser.quit()
    if server is not None:
        server.shutdown()

class ProviderTests(object):

    @classmethod
    def require_provider(cls, name):
        if name not in config.get('test_providers', []):
            raise SkipTest('tests not enabled for "%s"' % name)

    def setUp(self):
        browser.delete_all_cookies()

def find_login_url(config, key):
    return config.get(key, config['default_login_url'])

class TestFacebook(ProviderTests, unittest.TestCase):
    """
    TODO: look into adding multiple tests using test users with varying
          levels of functionality.

          http://developers.facebook.com/docs/test_users/
    """

    @classmethod
    def setUpClass(cls):
        cls.require_provider('facebook')
        cls.login = config['facebook.login']
        cls.password = config['facebook.password']
        cls.app = config['facebook.app']
        cls.login_url = find_login_url(config, 'facebook.login_url')

    def test_it(self):
        browser.get(self.login_url)
        self.assertEqual(browser.title, 'Auth Page')
        browser.find_element_by_id('facebook').submit()
        self.assertTrue('Facebook' in browser.title)
        form = browser.find_element_by_id('login_form')
        login = form.find_element_by_name('email')
        login.send_keys(self.login)
        passwd = form.find_element_by_name('pass')
        passwd.send_keys(self.password)
        form.submit()
        find_title = EC.title_is('Facebook')
        find_result = EC.presence_of_element_located((By.ID, 'result'))
        WebDriverWait(browser, 2).until(
            lambda driver: find_title(driver) or find_result(driver))
        while browser.title == 'Facebook':
            btn = WebDriverWait(browser, 2).until(
                EC.presence_of_element_located((By.NAME, '__CONFIRM__')))
            btn.click()
            WebDriverWait(browser, 2).until(
                lambda driver: find_title(driver) or find_result(driver))
        result = browser.find_element_by_id('result')
        self.assertEqual(browser.title, 'Result Page')
        result = json.loads(result.text)
        self.assertTrue('profile' in result)
        self.assertTrue('credentials' in result)
        profile = result['profile']
        self.assertTrue('emails' in profile)
        self.assertTrue('displayName' in profile)
        self.assertTrue('accounts' in profile)
        creds = result['credentials']
        self.assertTrue('oauthAccessToken' in creds)

class TestGithub(ProviderTests, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.require_provider('github')
        cls.login = config['github.login']
        cls.password = config['github.password']
        cls.app = config['github.app']
        cls.login_url = find_login_url(config, 'github.login_url')

    def test_it(self):
        browser.get(self.login_url)
        self.assertEqual(browser.title, 'Auth Page')
        browser.find_element_by_id('github').submit()
        self.assertEqual(browser.title,
                         b'Sign in \xc2\xb7 GitHub'.decode('utf-8'))
        form = browser.find_element_by_id('login')
        login = form.find_element_by_name('login')
        login.send_keys(self.login)
        passwd = form.find_element_by_name('password')
        passwd.send_keys(self.password)
        form.find_element_by_name('commit').submit()
        find_title = EC.title_is('Authorize access to your account')
        find_result = EC.presence_of_element_located((By.ID, 'result'))
        WebDriverWait(browser, 2).until(
            lambda driver: find_title(driver) or find_result(driver))
        if browser.title == 'Authorize access to your account':
            btn = WebDriverWait(browser, 2).until(
                EC.presence_of_element_located((By.NAME, 'authorize')))
            btn.click()
            result = WebDriverWait(browser, 2).until(
                EC.presence_of_element_located((By.ID, 'result')))
        else:
            result = browser.find_element_by_id('result')
        self.assertEqual(browser.title, 'Result Page')
        result = browser.find_element_by_id('result').text
        result = json.loads(result)
        self.assertTrue('profile' in result)
        self.assertTrue('credentials' in result)
        profile = result['profile']
        self.assertTrue('displayName' in profile)
        self.assertTrue('accounts' in profile)
        creds = result['credentials']
        self.assertTrue('oauthAccessToken' in creds)

class TestTwitter(ProviderTests, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.require_provider('twitter')
        cls.login = config['twitter.login']
        cls.password = config['twitter.password']
        cls.app = config['twitter.app']
        cls.login_url = find_login_url(config, 'twitter.login_url')

    def test_it(self):
        browser.get(self.login_url)
        self.assertEqual(browser.title, 'Auth Page')
        browser.find_element_by_id('twitter').submit()
        self.assertEqual(browser.title, 'Twitter / Authorize an application')
        app_info = browser.find_elements_by_class_name('app-info')[0]
        self.assertTrue(self.app in app_info.text)
        form = browser.find_element_by_id('oauth_form')
        login = form.find_element_by_id('username_or_email')
        login.send_keys(self.login)
        passwd = form.find_element_by_id('password')
        passwd.send_keys(self.password)
        form.find_element_by_id('allow').submit()
        result = WebDriverWait(browser, 2).until(
            EC.presence_of_element_located((By.ID, 'result')))
        self.assertEqual(browser.title, 'Result Page')
        result = json.loads(result.text)
        self.assertTrue('profile' in result)
        self.assertTrue('credentials' in result)
        profile = result['profile']
        self.assertTrue('displayName' in profile)
        self.assertTrue('accounts' in profile)
        creds = result['credentials']
        self.assertTrue('oauthAccessToken' in creds)
        self.assertTrue('oauthAccessTokenSecret' in creds)

class TestBitbucket(ProviderTests, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.require_provider('bitbucket')
        cls.login = config['bitbucket.login']
        cls.password = config['bitbucket.password']
        cls.app = config['bitbucket.app']
        cls.login_url = find_login_url(config, 'bitbucket.login_url')

    def test_it(self):
        browser.get(self.login_url)
        self.assertEqual(browser.title, 'Auth Page')
        browser.find_element_by_id('bitbucket').submit()
        self.assertEqual(browser.title,
                         b'Log in \xe2\x80\x94 Bitbucket'.decode('utf-8'))
        login = browser.find_element_by_id('id_username')
        login.send_keys(self.login)
        passwd = browser.find_element_by_id('id_password')
        passwd.send_keys(self.password)
        passwd.submit()
        result = WebDriverWait(browser, 2).until(
            EC.presence_of_element_located((By.ID, 'result')))
        self.assertEqual(browser.title, 'Result Page')
        result = json.loads(result.text)
        self.assertTrue('profile' in result)
        self.assertTrue('credentials' in result)
        profile = result['profile']
        self.assertTrue('displayName' in profile)
        self.assertTrue('accounts' in profile)
        creds = result['credentials']
        self.assertTrue('oauthAccessToken' in creds)
        self.assertTrue('oauthAccessTokenSecret' in creds)

class TestGoogleHybrid(ProviderTests, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.require_provider('google_hybrid')
        cls.login = config['google_hybrid.login']
        cls.password = config['google_hybrid.password']
        cls.login_url = find_login_url(config, 'google_hybrid.login_url')

    def test_it(self):
        browser.get(self.login_url)
        self.assertEqual(browser.title, 'Auth Page')
        browser.find_element_by_id('google_hybrid').submit()
        login = WebDriverWait(browser, 2).until(
            EC.presence_of_element_located((By.ID, 'Email')))
        self.assertEqual(browser.title, 'Google Accounts')
        login.send_keys(self.login)
        passwd = browser.find_element_by_id('Passwd')
        passwd.send_keys(self.password)
        passwd.submit()
        find_title = EC.title_is('Request for Permission')
        find_result = EC.presence_of_element_located((By.ID, 'result'))
        WebDriverWait(browser, 2).until(
            lambda driver: find_title(driver) or find_result(driver))
        if browser.title == 'Request for Permission':
            btn = WebDriverWait(browser, 2).until(
                EC.element_to_be_clickable(
                    (By.ID, 'submit_approve_access')))
            btn.click()
            result = WebDriverWait(browser, 2).until(
                EC.presence_of_element_located((By.ID, 'result')))
        else:
            result = browser.find_element_by_id('result')
        self.assertEqual(browser.title, 'Result Page')
        result = json.loads(result.text)
        self.assertTrue('profile' in result)
        self.assertTrue('credentials' in result)
        profile = result['profile']
        self.assertTrue('displayName' in profile)
        self.assertTrue('accounts' in profile)
        self.assertTrue('emails' in profile)
        creds = result['credentials']
        self.assertTrue('oauthAccessToken' in creds)
        self.assertTrue('oauthAccessTokenSecret' in creds)

class TestGoogleOAuth2(ProviderTests, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.require_provider('google_oauth2')
        cls.login = config['google_oauth2.login']
        cls.password = config['google_oauth2.password']
        cls.login_url = find_login_url(config, 'google_oauth2.login_url')

    def test_it(self):
        browser.get(self.login_url)
        self.assertEqual(browser.title, 'Auth Page')
        browser.find_element_by_id('google_oauth2').submit()
        login = WebDriverWait(browser, 2).until(
            EC.presence_of_element_located((By.ID, 'Email')))
        self.assertEqual(browser.title, 'Google Accounts')
        login.send_keys(self.login)
        passwd = browser.find_element_by_id('Passwd')
        passwd.send_keys(self.password)
        passwd.submit()
        find_title = EC.title_is('Request for Permission')
        find_result = EC.presence_of_element_located((By.ID, 'result'))
        WebDriverWait(browser, 2).until(
            lambda driver: find_title(driver) or find_result(driver))
        if browser.title == 'Request for Permission':
            btn = WebDriverWait(browser, 2).until(
                EC.element_to_be_clickable(
                    (By.ID, 'submit_approve_access')))
            btn.click()
            result = WebDriverWait(browser, 2).until(
                EC.presence_of_element_located((By.ID, 'result')))
        else:
            result = browser.find_element_by_id('result')
        self.assertEqual(browser.title, 'Result Page')
        result = json.loads(result.text)
        self.assertTrue('profile' in result)
        self.assertTrue('credentials' in result)
        profile = result['profile']
        self.assertTrue('displayName' in profile)
        self.assertTrue('accounts' in profile)
        self.assertTrue('emails' in profile)
        creds = result['credentials']
        self.assertTrue('oauthAccessToken' in creds)
        self.assertTrue('oauthRefreshToken' in creds)

class TestYahoo(ProviderTests, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.require_provider('yahoo')
        cls.login = config['yahoo.login']
        cls.password = config['yahoo.password']
        cls.login_url = find_login_url(config, 'yahoo.login_url')

    def test_it(self):
        browser.get(self.login_url)
        self.assertEqual(browser.title, 'Auth Page')
        browser.find_element_by_id('yahoo').submit()
        WebDriverWait(browser, 2).until(
            EC.presence_of_element_located((By.ID, 'username')))
        self.assertEqual(browser.title, 'Sign in to Yahoo!')
        login = browser.find_element_by_id('username')
        login.send_keys(self.login)
        passwd = browser.find_element_by_id('passwd')
        passwd.send_keys(self.password)
        passwd.submit()
        # there may be a captcha here, possibly wait for user input???
        find_alert = EC.alert_is_present()
        find_auth_agree = EC.presence_of_element_located((By.ID, 'agree'))
        WebDriverWait(browser, 2).until(
            lambda driver: find_alert(driver) or find_auth_agree(driver))
        auth_agree = browser.find_element_by_id('agree')
        if auth_agree:
            auth_agree.click()
            alert = WebDriverWait(browser, 2).until(EC.alert_is_present())
        else:
            alert = browser.switch_to_alert()
        alert.accept()
        result = WebDriverWait(browser, 5).until(
            EC.presence_of_element_located((By.ID, 'result')))
        self.assertEqual(browser.title, 'Result Page')
        result = json.loads(result.text)
        self.assertTrue('profile' in result)
        self.assertTrue('credentials' in result)
        profile = result['profile']
        self.assertTrue('displayName' in profile)
        self.assertTrue('accounts' in profile)
        self.assertTrue('emails' in profile)
        creds = result['credentials']
        self.assertTrue('oauthAccessToken' in creds)
        self.assertTrue('oauthAccessTokenSecret' in creds)

class TestWindowsLive(ProviderTests, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.require_provider('live')
        cls.login = config['live.login']
        cls.password = config['live.password']
        cls.login_url = find_login_url(config, 'live.login_url')

    def test_it(self):
        browser.get(self.login_url)
        self.assertEqual(browser.title, 'Auth Page')
        browser.find_element_by_id('live').submit()
        WebDriverWait(browser, 2).until(
            EC.presence_of_element_located((By.NAME, 'login')))
        self.assertEqual(browser.title,
                         'Sign in to your Microsoft account')
        login = browser.find_element_by_name('login')
        login.send_keys(self.login)
        passwd = browser.find_element_by_name('passwd')
        passwd.send_keys(self.password)
        passwd.submit()
        find_title = EC.title_is('Allow access?')
        find_result = EC.presence_of_element_located((By.ID, 'result'))
        WebDriverWait(browser, 2).until(
            lambda driver: find_title(driver) or find_result(driver))
        if browser.title == 'Allow access?':
            btn = WebDriverWait(browser, 2).until(
                EC.presence_of_element_located((By.NAME, 'submitYes')))
            btn.click()
            result = WebDriverWait(browser, 2).until(
                EC.presence_of_element_located((By.ID, 'result')))
        else:
            result = browser.find_element_by_id('result')
        self.assertEqual(browser.title, 'Result Page')
        result = json.loads(result.text)
        self.assertTrue('profile' in result)
        self.assertTrue('credentials' in result)
        profile = result['profile']
        self.assertTrue('displayName' in profile)
        self.assertTrue('accounts' in profile)
        creds = result['credentials']
        self.assertTrue('oauthAccessToken' in creds)

class TestOpenID(ProviderTests, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.require_provider('openid')
        cls.login = config['openid.login']
        cls.password = config['openid.password']
        cls.login_url = find_login_url(config, 'openid.login_url')

    def test_it(self):
        browser.get(self.login_url)
        self.assertEqual(browser.title, 'Auth Page')
        browser.find_element_by_id('openid').submit()
        login = WebDriverWait(browser, 2).until(
            EC.presence_of_element_located((By.NAME, 'user_name')))
        self.assertEqual(browser.title, 'Sign In')
        login.send_keys(self.login)
        passwd = browser.find_element_by_name('password')
        passwd.send_keys(self.password)
        passwd.submit()
        find_alert = EC.alert_is_present()
        find_continue = EC.presence_of_element_located(
            (By.ID, 'continue-button'))
        result = WebDriverWait(browser, 2).until(
            lambda driver: find_alert(driver) or find_continue(driver))
        if isinstance(result, Alert):
            alert = browser.switch_to_alert()
        else:
            result.click()
            alert = WebDriverWait(browser, 2).until(EC.alert_is_present())
        alert.accept()
        result = WebDriverWait(browser, 2).until(
            EC.presence_of_element_located((By.ID, 'result')))
        self.assertEqual(browser.title, 'Result Page')
        result = json.loads(result.text)
        self.assertTrue('profile' in result)
        self.assertTrue('credentials' in result)
        profile = result['profile']
        self.assertTrue('name' in profile)
        self.assertTrue('accounts' in profile)

class TestLinkedin(ProviderTests, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.require_provider('linkedin')
        cls.login = config['linkedin.login']
        cls.password = config['linkedin.password']
        cls.login_url = find_login_url(config, 'linkedin.login_url')

    def test_it(self):
        browser.get(self.login_url)
        self.assertEqual(browser.title, 'Auth Page')
        browser.find_element_by_id('linkedin').submit()
        self.assertEqual(browser.title, 'Authorize | LinkedIn')
        form = browser.find_element_by_name('oauthAuthorizeForm')
        login = form.find_element_by_id('session_key-oauthAuthorizeForm')
        login.send_keys(self.login)
        passwd = form.find_element_by_id('session_password-oauthAuthorizeForm')
        passwd.send_keys(self.password)
        form.find_element_by_name('authorize').submit()
        result = WebDriverWait(browser, 2).until(
            EC.presence_of_element_located((By.ID, 'result')))
        self.assertEqual(browser.title, 'Result Page')
        result = json.loads(result.text)
        self.assertTrue('profile' in result)
        self.assertTrue('credentials' in result)
        profile = result['profile']
        self.assertTrue('displayName' in profile)
        self.assertTrue('accounts' in profile)
        # BBB: Linkedin app must be enabled toshare e-mail
        self.assertTrue('emails' in profile)
        creds = result['credentials']
        self.assertTrue('oauthAccessToken' in creds)
        self.assertTrue('oauthAccessTokenSecret' in creds)
