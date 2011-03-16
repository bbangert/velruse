import time

import lettuce_webdriver.webdriver

def wait_for_elem(browser, xpath):
    elems = []
    while not elems:
        elems = browser.find_elements_by_xpath(xpath)
        if not elems:
            time.sleep(0.2)
    return elems
