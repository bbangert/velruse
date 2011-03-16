import time

from lettuce import step
from lettuce import world
import lettuce_webdriver.webdriver

def wait_for_elem(browser, xpath):
    elems = []
    while not elems:
        elems = browser.find_elements_by_xpath(xpath)
        if not elems:
            time.sleep(0.2)
    return elems

@step('I go to the velruse login page')
def login_page(step):
    world.browser.get(world.login_page)


@step('I have no cookies')
def no_cookies(step):
    world.browser.delete_all_cookies()
