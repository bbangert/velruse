Feature: Google testing
    In order to use velruse worth a shit
    As a programming guru
    I want the damn code to actually work
    
    Scenario: Authorizing google while being logged in
        Given I am logged into Google
            And I have not authorized the Google app
            And I go to the velruse login page
        When I press "Login with Google"
            And I should see "asking for some information from your Google Account" within 5 seconds
            And I should see "Remember this approval"
            And I press "Allow"
        Then I should see "ok" within 5 seconds
            And I should see "displayName"
            And I should see "Google"
            And I should see "oauthAccessToken"
