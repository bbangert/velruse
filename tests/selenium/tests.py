import unittest

browser = None # populated in setUpModule

BASE_URL = 'http://localhost:5000'

def setUpModule():
    from selenium import webdriver
    global browser
    browser = webdriver.Firefox()
    return browser

def tearDownModule():
    browser.quit()

class TestDummy(unittest.TestCase):
    def test_it(self):
        browser.get(BASE_URL+'/login')
        browser.

if __name__ == '__main__':
    setUpModule()
    try:
        unittest.main()
    except:
        tearDownModule()
