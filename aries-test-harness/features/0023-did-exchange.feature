@RFC0023 @AIP20
Feature: RFC 0023 Establishing Connections with DID Exchange
   In order establish a connection with two parties,
   As a responder or a requester,
   I want to use DID Exchange(RFC0023) and Out of Band(RFC0434) protocols to accomplish this.


   @T001-RFC0023 @critical @AcceptanceTest
   Scenario: Establish a connection with DID Exchange between two agents with an explicit invitation
      Given we have "2" agents
         | name | role      |
         | Acme | requester |
         | Bob  | responder |
      When "Bob" sends an explicit invitation
      And "Acme" receives the invitation
      And "Acme" sends the request to "Bob"
      And "Bob" receives the request
      And "Bob" sends a response to "Acme"
      And "Acme" receives the response
      And "Acme" sends complete to "Bob"
      Then "Acme" and "Bob" have a connection

   @T002-RFC0023 @critical @AcceptanceTest
   Scenario: Establish a connection with DID Exchange between two agents with an explicit invitation with role reversal
      Given we have "2" agents
         | name | role      |
         | Acme | responder |
         | Bob  | requester |
      When "Acme" sends an explicit invitation
      And "Bob" receives the invitation
      And "Bob" sends the request to "Acme"
      And "Acme" receives the request
      And "Acme" sends a response to "Bob"
      And "Bob" receives the response
      And "Bob" sends complete to "Acme"
      Then "Bob" and "Acme" have a connection

   @T003-RFC0023 @normal @AcceptanceTest
   Scenario: Establish a connection with DID Exchange between two agents with an explicit invitation with a public DID
      Given we have "2" agents
         | name | role      |
         | Acme | requester |
         | Bob  | responder |
      When "Bob" sends an explicit invitation with a public DID
      And "Acme" receives the invitation
      And "Acme" sends the request to "Bob"
      And "Bob" receives the request
      And "Bob" sends a response to "Acme"
      And "Acme" receives the response
      And "Acme" sends complete to "Bob"
      Then "Acme" and "Bob" have a connection

   @T004-RFC0023 @normal @AcceptanceTest
   Scenario: Establish a connection with DID Exchange between two agents with an explicit invitation with a public DID with role reversal
      Given we have "2" agents
         | name | role      |
         | Acme | responder |
         | Bob  | requester |
      When "Acme" sends an explicit invitation with a public DID
      And "Bob" receives the invitation
      And "Bob" sends the request to "Acme"
      And "Acme" receives the request
      And "Acme" sends a response to "Bob"
      And "Bob" receives the response
      And "Bob" sends complete to "Acme"
      Then "Bob" and "Acme" have a connection

   @T005-RFC0023 @critical @AcceptanceTest
   Scenario: Establish a connection with DID Exchange between two agents with an implicit invitation
      Given we have "2" agents
         | name | role      |
         | Acme | requester |
         | Bob  | responder |
      And "Bob" has a resolvable DID
      And "Acme" acquires the resolvable DID
      When "Acme" sends the request to "Bob" with the public DID
      And "Bob" receives the request with their public DID
      When "Bob" sends a response to "Acme"
      And "Acme" receives the response
      And "Acme" sends complete to "Bob"
      Then "Acme" and "Bob" have a connection

   @T006-RFC0023 @critical @AcceptanceTest
   Scenario: Establish a connection with DID Exchange between two agents with an implicit invitation with role reversal
      Given we have "2" agents
         | name | role      |
         | Acme | responder |
         | Bob  | requester |
      And "Acme" has a resolvable DID
      And "Bob" acquires the resolvable DID
      When "Bob" sends the request to "Acme" with the public DID
      And "Acme" receives the request with their public DID
      And "Acme" sends a response to "Bob"
      And "Bob" receives the response
      And "Bob" sends complete to "Acme"
      Then "Bob" and "Acme" have a connection

   @T007-RFC0023 @normal @AcceptanceTest @NegativeTest @ExceptionTest
   Scenario: Establish a connection with DID Exchange between two agents with attempt to continue after protocol is completed
      Given we have "2" agents
         | name | role      |
         | Acme | requester |
         | Bob  | responder |
      When "Bob" sends an explicit invitation
      And "Acme" receives the invitation
      And "Acme" sends the request to "Bob"
      And "Bob" receives the request
      And "Bob" sends a response to "Acme"
      And "Acme" receives the response
      And "Acme" sends complete to "Bob"
      And "Bob" sends a response to "Acme" which produces a problem_report
      Then "Acme" and "Bob" still have a completed connection

   @T008-RFC0023 @normal @AcceptanceTest @ExceptionTest @wip
   Scenario: Establish a connection with DID Exchange between two agents with an explicit invitation but invitation is rejected and connection process restarted
      Given we have "2" agents
         | name | role      |
         | Acme | requester |
         | Bob  | responder |
      When "Bob" sends an implicit invitation
      And "Acme" receives the invitation
      And "Acme" rejects the invitation
      And "Acme" restarts the connection process
      Then a successful connection can be established between "Acme" and "Bob"

   @T009-RFC0023 @normal @AcceptanceTest @ExceptionTest @wip
   Scenario: Establish a connection with DID Exchange between two agents with an explicit invitation but invitation is rejected and connection process abandoned
      Given we have "2" agents
         | name | role      |
         | Acme | requester |
         | Bob  | responder |
      When "Bob" sends an implicit invitation
      And "Acme" receives the invitation
      And "Acme" rejects the invitation
      And "Acme" abandons the connection process
      Then a connection can be established between "Acme" and "Bob" given that invitation

   @T010-RFC0023 @normal @AcceptanceTest @ExceptionTest @NegativeTest @wip
   Scenario Outline: Establish a connection with DID Exchange and responder rejects the request
      Given we have "2" agents
         | name | role      |
         | Acme | requester |
         | Bob  | responder |
      When "Bob" sends an explicit invitation
      And "Acme" receives the invitation
      And "Acme" sends the request to "Bob"
      And "Bob" receives the request
      And "Bob" rejects the request because of <reason>
      Then the connection is abandoned
      And "Acme" and "Bob" do not have a connection
      And establishing the connection cannot be continued

      Examples:
         | reason                                  |
         | Unsupported DID method for provided DID |
         | Expired Invitation                      |
         | DID Doc Invalid                         |
         | Unsupported key type                    |
         | Unsupported endpoint protocol           |
         | Missing reference to invitation         |
         | unknown processing error                |

   @T011-RFC0023 @normal @AcceptanceTest @ExceptionTest @NegativeTest @wip
   Scenario Outline: Establish a connection with DID Exchange and requester rejects the response
      Given we have "2" agents
         | name | role      |
         | Acme | requester |
         | Bob  | responder |
      When "Bob" sends an explicit invitation
      And "Acme" receives the invitation
      And "Acme" sends the request to "Bob"
      And "Bob" receives the request
      And "Bob" sends a response to "Acme"
      And "Acme" receives the response
      And "Acme" rejects the response because of <reason>
      Then the connection is abandoned
      And "Acme" and "Bob" do not have a connection
      And establishing the connection cannot be continued

      Examples:
         | reason                                  |
         | Unsupported DID method for provided DID |
         | Expired request                         |
         | DID Doc Invalid                         |
         | Unsupported key type                    |
         | Unsupported endpoint protocol           |
         | Invalid signature                       |
         | unknown processing error                |