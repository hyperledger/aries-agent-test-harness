@RFC0025 @AIP20 @UsesCustomParameters @DIDExchangeConnection
Feature: RFC 0025 DIDComm Transports
  In order to communicate with other agents,
  As an Agent
  I want to various transport protocol.

  @T001-RFC0025
  Scenario Outline: Create connection between two agents with overlapping transports
    Given we have "2" agents
      | name | role      |
      | Acme | responder |
      | Bob  | requester |
    And "Acme" is running with parameters "{"inbound_transports": <acme-inbound-transports>, "outbound_transports": <acme-outbound-transports> }"
    And "Bob" is running with parameters "{"inbound_transports": <bob-inbound-transports>, "outbound_transports": <bob-outbound-transports> }"

    When "Acme" and "Bob" create a new connection

    Then the invitation serviceEndpoint should use the "<acme-inbound-transports>" protocol scheme

    @Transport_Http
    Examples: DIDExchange connection with both agents using HTTP for inbound and outbound transport
      | acme-inbound-transports | acme-outbound-transports | bob-inbound-transports | bob-outbound-transports |
      | ["http"]                | ["http"]                 | ["http"]               | ["http"]                |

    @Transport_Ws @Transport_NoHttpOutbound
    Examples: DIDExchange connection with both agents using WS for inbound and outbound transport
      | acme-inbound-transports | acme-outbound-transports | bob-inbound-transports | bob-outbound-transports |
      | ["ws"]                  | ["ws"]                   | ["ws"]                 | ["ws"]                  |

    # This test is basically the same as the one above, but mainly for ACA-Py that doesn't support running without
    # HTTP outbound, as it uses the HTTP outbound transport to send webhook events.
    @Transport_Ws @Transport_Http
    Examples: DIDExchange connection with both agents using WS for inbound and outbound transport, but also supporting http for outbound transport
      | acme-inbound-transports | acme-outbound-transports | bob-inbound-transports | bob-outbound-transports |
      | ["ws"]                  | ["ws", "http"]           | ["ws"]                 | ["ws", "http"]          |

    @Transport_Http @Transport_Ws
    Examples: DIDExchange connection with both agents using HTTP and WS for inbound and outbound transport
      | acme-inbound-transports | acme-outbound-transports | bob-inbound-transports | bob-outbound-transports |
      | ["http", "ws"]          | ["http", "ws"]           | ["http", "ws"]         | ["http", "ws"]          |
      | ["ws", "http"]          | ["ws", "http"]           | ["ws", "http"]         | ["ws", "http"]          |

    @Transport_Http @Transport_Ws
    Examples: DIDExchange connection with one agent using http for inbound and the other using ws and both agents supporting ws and http outbound
      | acme-inbound-transports | acme-outbound-transports | bob-inbound-transports | bob-outbound-transports |
      | ["http"]                | ["ws", "http"]           | ["ws"]                 | ["ws", "http"]          |
      | ["ws"]                  | ["ws", "http"]           | ["http"]               | ["ws", "http"]          |

  @T002-RFC0025
  Scenario Outline: Fail creating a connection between two agents that have mismatching transports configured
    Given we have "2" agents
      | name | role      |
      | Acme | responder |
      | Bob  | requester |
    And "Acme" is running with parameters "{"inbound_transports": <acme-inbound-transports>, "outbound_transports": <acme-outbound-transports> }"
    And "Bob" is running with parameters "{"inbound_transports": <bob-inbound-transports>, "outbound_transports": <bob-outbound-transports> }"

    When "Acme" sends an explicit invitation to "Bob"
    And "Bob" receives the invitation
    When "Bob" sends the request to "Acme"
    Then "Acme" does not receive the request

    @Transport_Http @Transport_Ws
    Examples: Both agents having no overlap in inbound and outbound transports
      | acme-inbound-transports | acme-outbound-transports | bob-inbound-transports | bob-outbound-transports |
      | ["ws"]                  | ["http"]                 | ["ws"]                 | ["http"]                |