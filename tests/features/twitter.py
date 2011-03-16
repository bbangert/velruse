from lettuce import step
from lettuce import world

from steps import wait_for_elem


@step('I am logged into Twitter')    
def logged_into_facebook(step):
    step.given('I have no cookies')
    step.given('I go to "http://twitter.com/"')
    step.given('I should see "Sign in"')
    world.browser.find_element_by_partial_link_text('Sign in').click()
    step.given('I fill in "username" with "%s"' % world.twitter_username)
    step.given('I fill in "password" with "%s"' % world.twitter_password)
    step.given('I press "Sign in"')
    elems = wait_for_elem(world.browser, '//*[contains(., "Your Tweets")]', 4)
    if not elems:
        world.browser.refresh()
    elems = wait_for_elem(world.browser, '//*[contains(., "Your Tweets")]', 4)


@step('I have not authorized the Twitter app')
def not_authorized_facebook_app(step):
    b = world.browser
    b.get('http://twitter.com/settings/connections')
    elem = b.find_elements_by_xpath(
        '//li[contains(.//label//*, "%s")]//a[@class="revoke-access"]' % world.twitter_app_name
    )
    if elem:
        elem[0].click()
    b.refresh()
