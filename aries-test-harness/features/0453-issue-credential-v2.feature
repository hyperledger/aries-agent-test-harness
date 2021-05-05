@RFC0453 @AIP20
Feature: RFC 0453 Aries Agent Issue Credential v2

  @T001-RFC0453 @RFC0592 @critical @AcceptanceTest @DIDExchangeConnection
  Scenario Outline: Issue a Credential with the Holder beginning with a proposal
    Given "2" agents
      | name | role   |
      | Acme | issuer |
      | Bob  | holder |
    Given "Acme" is ready to issue a "<credential_format>" credential
    And "Acme" and "Bob" have an existing connection
    When "Bob" proposes a "<credential_format>" credential to "Acme" with <credential_data>
    And "Acme" offers the "<credential_format>" credential
    And "Bob" requests the "<credential_format>" credential
    And "Acme" issues the "<credential_format>" credential
    And "Bob" acknowledges the "<credential_format>" credential issue
    Then "Bob" has the "<credential_format>" credential issued

    @CredFormat_Indy @Schema_DriversLicense_v2 @DidMethod_sov
    Examples: Indy
      | credential_data   | credential_format |
      | Data_DL_MaxValues | indy              |

    @CredFormat_JSON-LD @Schema_DriversLicense_v2 @ProofType_Ed25519Signature2018 @DidMethod_key
    Examples: Json-LD
      | credential_data   | credential_format |
      | Data_DL_MaxValues | json-ld           |

    @CredFormat_JSON-LD @Schema_DriversLicense_v2 @ProofType_BbsBlsSignature2020 @DidMethod_key
    Examples: Json-LD-BBS
      | credential_data   | credential_format |
      | Data_DL_MaxValues | json-ld           |


  @T002-RFC0453 @normal @wip @AcceptanceTest @DIDExchangeConnection @CredFormat_Indy @Schema_DriversLicense_v2
  Scenario Outline: Issue a credential with the Holder beginning with a proposal with negotiation
    Given "2" agents
      | name | role   |
      | Acme | issuer |
      | Bob  | holder |
    Given "Acme" has a public did
    And "Acme" is ready to issue a credential
    And "Acme" and "Bob" have an existing connection
    And "Bob" proposes a "indy" credential to "Acme" with <credential_data>
    And "Acme" offers the "indy" credential
    When "Bob" negotiates the offer with another proposal of the "indy" credential to "Acme" with <updated_credential_data>
    And "Acme" offers the "indy" credential
    And "Bob" requests the "indy" credential
    And "Acme" issues the "indy" credential
    And "Bob" acknowledges the "indy" credential issue
    Then "Bob" has the "indy" credential issued

    Examples:
      | credential_data   | updated_credential_data  |
      | Data_DL_MaxValues | Data_DL_NormalizedValues |

  # @T003-RFC0453 @critical @wip @AcceptanceTest
  # Scenario: Issue a credential with the Issuer beginning with an offer
  #   Given "2" agents
  #     | name | role   |
  #     | Acme | issuer |
  #     | Bob  | holder |
  #   And "Acme" and "Bob" have an existing connection
  #   When "Acme" offers a credential
  #   And "Bob" requests the credential
  #   And "Acme" issues the credential
  #   And "Bob" acknowledges the credential issue
  #   Then "Bob" has the credential issued

  # @T004-RFC0453 @normal @wip @AcceptanceTest
  # Scenario: Issue a credential with the Issuer beginning with an offer with negotiation
  #   Given "2" agents
  #     | name | role   |
  #     | Acme | issuer |
  #     | Bob  | holder |
  #   And "Acme" and "Bob" have an existing connection
  #   And "Acme" offers a credential
  #   When "Bob" negotiates the offer with a proposal of the credential to "Acme"
  #   And "Acme" Offers the credential
  #   And "Bob" requests the credential
  #   And "Acme" issues the credential
  #   And "Bob" acknowledges the credential issue
  #   Then "Bob" has the credential issued

  # @T005-RFC0453 @minor @wip @AcceptanceTest
  # Scenario: Issue a credential with negotiation beginning from a credential request
  #   Given "2" agents
  #     | name | role   |
  #     | Acme | issuer |
  #     | Bob  | holder |
  #   And "Acme" and "Bob" have an existing connection
  #   When "Bob" requests the credential
  #   And "Acme" offers a credential
  #   When "Bob" negotiates the offer with a proposal of the credential to "Acme"
  #   And "Acme" offers a credential
  #   And "Acme" issues the credential
  #   And "Bob" acknowledges the credential issue
  #   Then "Bob" has the credential issued

  # @T006-RFC0453 @critical @wip @AcceptanceTest
  # Scenario: Issue a credential with the Holder beginning with a request and is accepted
  #   Given "2" agents
  #     | name | role   |
  #     | Acme | issuer |
  #     | Bob  | holder |
  #   And "Acme" and "Bob" have an existing connection
  #   When "Bob" requests the credential
  #   And "Acme" issues the credential
  #   And "Bob" acknowledges the credential issue
  #   Then "Bob" has the credential issued
