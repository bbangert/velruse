import json
import os
import unittest2 as unittest
from ConfigParser import ConfigParser

from selenium import webdriver


config = {}
browser = None  # populated in setUpModule


def splitlines(s):
    return filter(None, [x.strip() for x in s.splitlines()])


def setUpModule():
    global browser, config

    inipath = os.environ.get('TEST_INI', 'testing.ini')
    if os.path.isfile(inipath):
        parser = ConfigParser()
        parser.read(inipath)

        config = dict(parser.items('testconfig'))
        config['test_providers'] = splitlines(config['test_providers'])
        config['base_url'] = 'http://localhost:5000'

    driver = config.get('selenium.driver', 'firefox')
    browser = {
        'firefox': webdriver.Firefox,
        'chrome': webdriver.Chrome,
        'ie': webdriver.Ie,
    }[driver]()


def tearDownModule():
    if browser is not None:
        browser.quit()


class ProviderTests(object):

    @classmethod
    def require_provider(cls, name):
        if name not in config.get('test_providers', []):
            raise unittest.SkipTest('tests not enabled for "%s"' % name)


class TestFacebook(ProviderTests, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.require_provider('facebook')
        cls.login = config['facebook.login']
        cls.password = config['facebook.password']
        cls.app = config['facebook.app']

    def setUp(self):
        browser.delete_all_cookies()

    def test_it(self):
        browser.get(config['base_url'] + '/login')
        self.assertEqual(browser.title, 'Auth Page')
        browser.find_element_by_id('facebook').submit()
        self.assertEqual(browser.title, 'Log In | Facebook')
        form = browser.find_element_by_id('login_form')
        login = form.find_element_by_name('email')
        login.send_keys(self.login)
        passwd = form.find_element_by_name('pass')
        passwd.send_keys(self.password)
        self.assertTrue(self.app in form.text)
        form.submit()
        self.assertEqual(browser.title, 'Result Page')
        result = browser.find_element_by_id('result').text
        result = json.loads(result)
        self.assertTrue('profile' in result)
        self.assertTrue('credentials' in result)
        self.assertTrue('displayName' in result['profile'])
        self.assertTrue('verifiedEmail' in result['profile'])
        self.assertTrue('accounts' in result['profile'])


class TestGithub(ProviderTests, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.require_provider('github')
        cls.login = config['github.login']
        cls.password = config['github.password']
        cls.app = config['github.app']

    def setUp(self):
        browser.delete_all_cookies()

    def test_it(self):
        browser.get(config['base_url'] + '/login')
        self.assertEqual(browser.title, 'Auth Page')
        browser.find_element_by_id('github').submit()
        self.assertEqual(browser.title, 'Log in - GitHub')
        form = browser.find_element_by_id('login')
        login = form.find_element_by_name('login')
        login.send_keys(self.login)
        passwd = form.find_element_by_name('password')
        passwd.send_keys(self.password)
        form.find_element_by_name('commit').submit()
        self.assertEqual(browser.title, 'Result Page')
        result = browser.find_element_by_id('result').text
        result = json.loads(result)
        self.assertTrue('profile' in result)
        self.assertTrue('credentials' in result)
        self.assertTrue('displayName' in result['profile'])
        self.assertTrue('accounts' in result['profile'])


if __name__ == '__main__':
    unittest.main()
