import json
import logging
import os
import unittest2 as unittest
from ConfigParser import ConfigParser


log = logging.getLogger(__name__)
config = {}
browser = None # populated in setUpModule


def splitlines(s):
    return filter(None, [x.strip() for x in s.splitlines()])


def setUpModule():
    from selenium import webdriver
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


class ProviderTestCase(unittest.TestCase):

    @classmethod
    def require_provider(cls, name):
        if name not in config.get('test_providers', []):
            raise unittest.SkipTest('tests not enabled for "%s"' % name)


class TestFacebook(ProviderTestCase):
    @classmethod
    def setUpClass(cls):
        cls.require_provider('facebook')
        cls.email = config['facebook.email']
        cls.password = config['facebook.password']
        cls.app = config['facebook.app']

    def setUp(self):
        browser.delete_all_cookies()

    def test_it(self):
        browser.get(config['base_url'] + '/login')
        self.assertEqual(browser.title, 'Auth Page')
        browser.find_element_by_id('facebook').submit()
        form = browser.find_element_by_id('login_form')
        email = form.find_element_by_name('email')
        email.send_keys(self.email)
        passwd = form.find_element_by_name('pass')
        passwd.send_keys(self.password)
        form.submit()
        self.assertEqual(browser.title, 'Result Page')
        result = browser.find_element_by_id('result').text
        result = json.loads(result)
        self.assertTrue('profile' in result)
        self.assertTrue('credentials' in result)
        self.assertTrue('displayName' in result['profile'])
        self.assertTrue('verifiedEmail' in result['profile'])


if __name__ == '__main__':
    unittest.main()
