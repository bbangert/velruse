from lettuce import step
from lettuce import world

from steps import wait_for_elem


@step('I am logged into Google')    
def logged_into_google(step):
    step.given('I have no cookies')
    #ncr is needed to skip redirects like google.com.do and then get spanish text....
    step.given('I go to "http://google.com/ncr"')
    step.given('I should see "Sign in"')
    world.browser.find_element_by_partial_link_text('Sign in').click()
    step.given('I fill in "Email" with "%s"' % world.google_username)
    step.given('I fill in "Passwd" with "%s"' % world.google_password)
    step.given('I press "Sign in"')
    wait_for_elem(world.browser, '//*[contains(., "Jorge Vargas")]')

@step(u'And I have not authorized the Google app')
def and_i_have_not_authorized_the_google_app(step):
    assert True, 'This step must be implemented'

