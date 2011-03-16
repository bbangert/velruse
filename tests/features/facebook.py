from lettuce import step
from lettuce import world

from steps import wait_for_elem


@step('I am logged into Facebook')    
def logged_into_facebook(step):
    step.given('I have no cookies')
    step.given('I go to "http://www.facebook.com/"')
    step.given('I should see "Sign Up"')
    step.given('I fill in "Email" with "%s"' % world.facebook_email)
    step.given('I fill in "Password" with "%s"' % world.facebook_password)
    step.given('I press "Login"')
    wait_for_elem(world.browser, '//*[contains(., "News Feed")]')
    step.given('I should see "News Feed"')


@step('I have authorized the Facebook app')
def authorized_facebook_app(step):
    step.given('I go to "http://www.facebook.com/settings/?tab=applications"')


@step('I have not authorized the Facebook app')
def not_authorized_facebook_app(step):
    b = world.browser
    b.get('http://www.facebook.com/settings/?tab=applications')
    elems = b.find_elements_by_xpath('//span[contains(., "%s")]' % world.facebook_app_name)
    if elems:
        elems[0].click()
        wait_for_elem(b, '//a[contains(., "Remove app")]')[0].click()
        wait_for_elem(b, '//input[@type="button"][@value="Remove"]')[0].click()
        wait_for_elem(b, '//input[@type="button"][@value="Okay"]')[0].click()
