Feature: Facebook testing
    In order to use velruse worth a shit
    As a programming guru
    I want the damn code to actually work
    
    Scenario: Authorizing Facebook while being logged in
        Given I am logged into Facebook
            And I have not authorized the Facebook app
            And I go to the velruse login page
        When I press "Login with Facebook"
            And I should see "Logged in as" within 5 seconds
            And I should see "Send me email"
            And I press "Allow"
        Then I should see "ok" within 5 seconds
            And I should see "displayName"
            And I should see "verifiedEmail"
            And I should see "credentials"
