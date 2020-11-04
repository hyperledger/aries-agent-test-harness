Feature: Aries agent connection functions RFC 0160

   @T001-AIP10-RFC0160 @P1 @AcceptanceTest @RFC0160
   Scenario Outline: establish a connection between two agents
      Given we have "2" agents
         | name  | role    |
         | Acme | inviter |
         | Bob   | invitee |
      When "Acme" generates a connection invitation
      And "Bob" receives the connection invitation
      And "Bob" sends a connection request to "Acme"
      And "Acme" receives the connection request
      And "Acme" sends a connection response to "Bob"
      And "Bob" receives the connection response
      And "Bob" sends <message> to "Acme"
      Then "Acme" and "Bob" have a connection

      Examples:
         | message   |
         | trustping |
         # | acks      | *Note* in RFC 0302: Aries Interop Profile, it states that Acknowledgements are part of AIP 1.0, however, agents under test have
                        # implemented trustping which is not part of the AIP 1.0. The acks is removed here in favor of trustping until the RFC is changed or
                        # the agents under test implement acks.

   @T001.2-AIP10-RFC0160 @P1 @AcceptanceTest @RFC0160
   Scenario Outline: establish a connection between two agents with role reversal
      Given we have "2" agents
         | name  | role    |
         | Acme | invitee |
         | Bob   | inviter |
      When "Bob" generates a connection invitation
      And "Acme" receives the connection invitation
      And "Acme" sends a connection request to "Bob"
      And "Bob" receives the connection request
      And "Bob" sends a connection response to "Acme"
      And "Acme" receives the connection response
      And "Acme" sends <message> to "Bob"
      Then "Bob" and "Acme" have a connection

      Examples:
         | message   |
         | trustping |
         # | acks      | *Note* in RFC 0302: Aries Interop Profile, it states that Acknowledgements are part of AIP 1.0, however, agents under test have
                        # implemented trustping which is not part of the AIP 1.0. The acks is removed here in favor of trustping until the RFC is changed or
                        # the agents under test implement acks.


   @T002-AIP10-RFC0160 @P1 @AcceptanceTest @RFC0160
   Scenario Outline: Connection established between two agents but inviter sends next message to establish full connection state
      Given we have "2" agents
         | name  | role    |
         | Acme | inviter |
         | Bob   | invitee |
      When "Acme" generates a connection invitation
      And "Bob" receives the connection invitation
      And "Bob" sends a connection request to "Acme"
      And "Acme" receives the connection request
      And "Acme" sends a connection response to "Bob"
      And "Bob" receives the connection response
      And "Acme" sends <message> to "Bob"
      Then "Acme" and "Bob" have a connection

      Examples:
         | message   |
         | trustping |
         # | acks      | *Note* in RFC 0302: Aries Interop Profile, it states that Acknowledgements are part of AIP 1.0, however, agents under test have
                        # implemented trustping which is not part of the AIP 1.0. The acks is removed here in favor of trustping until the RFC is changed or
                        # the agents under test implement acks.


   @T003-AIP10-RFC0160 @SingleUseInvite @P2 @ExceptionTest @WillFail @OutstandingBug..418..https://github.com/hyperledger/aries-cloudagent-python/issues/418 @RFC0160
   Scenario: Inviter Sends invitation for one agent second agent tries after connection
      Given we have "3" agents
         | name    | role              |
         | Acme   | inviter           |
         | Bob     | invitee           |
         | Mallory | inviteinterceptor |
      And "Acme" generated a single-use connection invitation
      And "Bob" received the connection invitation
      And "Bob" sent a connection request to "Acme"
      And "Acme" receives the connection request
      And "Acme" sends a connection response to "Bob"
      And "Bob" receives the connection response
      And "Acme" and "Bob" have a connection
      When "Mallory" sends a connection request to "Acme" based on the connection invitation
      Then "Acme" sends a request_not_accepted error

@T004-AIP10-RFC0160 @SingleUseInvite @P2 @ExceptionTest @WillFail @OutstandingBug..418..https://github.com/hyperledger/aries-cloudagent-python/issues/418 @RFC0160
   Scenario: Inviter Sends invitation for one agent second agent tries during first share phase
      Given we have "3" agents
         | name    | role              |
         | Acme   | inviter           |
         | Bob     | invitee           |
         | Mallory | inviteinterceptor |
      And "Acme" generated a single-use connection invitation
      And "Bob" received the connection invitation
      And "Bob" sent a connection request to "Acme"
      When "Mallory" sends a connection request to "Acme" based on the connection invitation
      Then "Acme" sends a request_not_accepted error

   @T005-AIP10-RFC0160 @MultiUseInvite @P3 @DerivedFunctionalTest @NeedsReview @wip @RFC0160
   Scenario: Inviter Sends invitation for multiple agents
      Given we have "3" agents
         | name    | role              |
         | Acme   | inviter           |
         | Bob     | invitee           |
         | Mallory | inviteinterceptor |
      And "Acme" generated a multi-use connection invitation
      And "Bob" receives the connection invitation
      And "Bob" sends a connection request to "Acme"
      And "Acme" receives the connection request
      And "Acme" sends a connection response to "Bob"
      When "Mallory" sends a connection request to "Acme" based on the connection invitation
      Then "Acme" sends a connection response to "Mallory"
   #And "Acme" and "Bob" are able to complete the connection
   #And "Acme" and "Mallory" are able to complete the connection

   @T006-AIP10-RFC0160 @P4 @DerivedFunctionalTest @RFC0160
   Scenario: Establish a connection between two agents who already have a connection initiated from invitee
      Given we have "2" agents
         | name  | role    |
         | Acme | inviter |
         | Bob   | invitee |
      And "Acme" and "Bob" have an existing connection
      When "Bob" generates a connection invitation
      And "Bob" and "Acme" complete the connection process
      Then "Acme" and "Bob" have another connection

   @T007-AIP10-RFC0160 @P2 @ExceptionTest @SingleTryOnException @NeedsReview @RFC0160
   Scenario Outline: Establish a connection between two agents but gets a request not accepted report problem message
      Given we have "2" agents
         | name  | role    |
         | Acme | inviter |
         | Bob   | invitee |
      And "Bob" has <problem>
      When "Acme" generates a connection invitation
      And "Bob" receives the connection invitation
      And "Bob" sends a connection request to "Acme"
      Then "Acme" sends an request not accepted error
      And the state of "Acme" is reset to Null
      And the state of "Bob" is reset to Null

      Examples:
         | problem                    |
         | Invalid DID Method         |
         | unknown endpoint protocols |
