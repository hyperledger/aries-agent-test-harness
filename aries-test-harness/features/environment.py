# -----------------------------------------------------------
# Behave environment file used to hold test hooks to do
# Setup and Tear Downs at different levels
# For more info see:
# https://behave.readthedocs.io/en/latest/tutorial.html#environmental-controls
#  
# -----------------------------------------------------------
import json
from collections import defaultdict

def before_scenario(context, scenario):
    setup_scenario_context(context, scenario)
    
    # Check if the scenario has an issue associated
    for tag in context.tags:
        if '.issue:' in tag:
            
            # Parse out the URL in the issue tag.
            l_issue_info = tag.split(":")
            s_issue_url = 'https:' + l_issue_info[2]

            #get the test id for this scenario
            for tag in context.tags:
                if tag.startswith("T"):
                    test_id = tag
                    break

            # Tell the user the scenario will fail and the URL to the issue
            print ('NOTE: Test ' + test_id + ':' + scenario.name + ', WILL FAIL due to an outstanding issue not yet resolved.')
            print ('For more information see issue details at ' + s_issue_url)
            break

    # Check if the @MultiUseInvite tag exists
    if 'MultiUseInvite' in context.tags :
        
        print ('NOTE: Test \"' + scenario.name + '\" WILL FAIL if your Agent Under Test is not started with or does not support Multi Use Invites.')

    # Check for Present Proof Feature to be able to handle the loading of schemas and credential definitions before the scenarios.
    if 'present proof' in context.feature.name or 'revocation' in context.feature.name or 'Issue Credential' in context.feature.name:
            # get the tag with "Schema_".
            for tag in context.tags:
                if 'ProofType_' in tag:
                    # Get and assign the proof type to the context
                    # tag is in format "ProofType_PROOFTYPESTRING"
                    context.proof_type = tag.split("ProofType_")[1]
                if 'DidMethod_' in tag:
                    # Get and assign the did method to the context
                    # tag is in format "@DidMethod_DIDMETHOD"
                    context.did_method = tag.split("DidMethod_")[1]
                if 'Schema_' in tag:
                    # Get and assign the schema to the context
                    try:
                        schema_json_file = open('features/data/' + tag.lower() + '.json')
                        schema_json = json.load(schema_json_file)

                        # If this is issue credential then you can't created multiple credential defs at the same time, like Proof uses
                        # multiple credential types in the proof. So just set the context.schema here to be used in the issue cred test.
                        # This makes the rule that you can only have one @Schema_ tag in an issue credential test scenario. 
                        if 'Issue Credential' in context.feature.name:
                            context.schema = schema_json["schema"]
                            # Get and assign the credential definition info to the context
                            context.support_revocation = schema_json["cred_def_support_revocation"]

                        # Support multiple schemas for multiple creds in a proof request.
                        # for each schema in tags add the schema and revocation support to a dict keyed by schema name.

                        context.schema_dict[tag] = schema_json["schema"]
                        context.support_revocation_dict[tag] = schema_json["cred_def_support_revocation"]

                    except FileNotFoundError:
                        print('FileNotFoundError: features/data/' + tag.lower() + '.json')

def setup_scenario_context(context, scenario):
    """Prepare scenario context for test run"""

    # Agent urls and names
    # context.<name>_url = "http://192.168.65.3:9020"
    # context.<role>_name = "Alice"

    # holder
    context.holder_url = None
    context.holder_name = None

    # issuer
    context.issuer_url = None
    context.issuer_name = None

    # verifier
    context.verifier_url = None
    context.verifier_name = None

    # prover
    context.prover_url = None
    context.prover_name = None

    # inviter
    context.inviter_url = None
    context.inviter_name = None

    # invitee
    context.invitee_url = None
    context.invitee_name = None

    # inviteinterceptor
    context.inviteinterceptor_url = None
    context.inviteinterceptor_name = None

    # requester
    context.requester_url = None
    context.requester_name = None

    # responder
    context.responder_url = None
    context.responder_name = None

    # Agent name to connection id mapping
    # {
    #   "<agent_name>": "<connection_id>"
    # }
    # context.temp_connection_id_dict["Alice"] = "07da4b41-40e9-4f8e-8e7b-603430f5aac3"
    context.temp_connection_id_dict = {}

    # Schema name to credentail ids mapping
    # {
    #   "<schema_name>": ["<cred_id_stored>"]
    # } 
    # 
    # defaultdict allows to instantly append without creating list first
    # context.credential_id_dict["Schema_DriversLicense_v2"].append("799519c6-c635-46e4-a14d-9af52e79e894")
    context.credential_id_dict = defaultdict(list)

    # Whether revocation is supported
    context.support_revocation = False

    # TODO: is schema_name same as the schema tags used
    # {
    #   "<schema_name>": <supports_revocation_boolean>
    # }
    # 
    # context.support_revocation_dict["Schema_DriversLicense_v2"] = True
    context.support_revocation_dict = {}

    # Linked Data Proof credentials specific proof type indiciator
    # 
    # context.proof_type = "Ed25519Signature2018"
    context.proof_type = None

    # Indy loaded schema data
    # 
    # context.schema = {
    #   "schema_name":"Schema_DriversLicense_v2",
    #   "schema_version":"1.1.0",
    #   "attributes":[
    #       "address",
    #       "DL_number",
    #       "expiry",
    #       "age"
    #   ]
    # }
    context.schema = None

    # Credential data dict
    # {
    #   "<schema_name>": attributes_array 
    # }
    # 
    # context.credential_data_dict["Schema_Health_ID"] = [
    #    {
    #       "name":"address",
    #       "value":"947 this street, Kingston Ontario Canada, K9O 3R5"
    #    }
    # ]
    context.credential_data_dict = {}

    # Credential data
    # 
    # context.credential_data = [
    #    {
    #       "name":"address",
    #       "value":"947 this street, Kingston Ontario Canada, K9O 3R5"
    #    }
    # ]
    context.credential_data = None

    # Store cred revocation creation time?
    # 
    # context.cred_rev_creation_time = time.time()
    context.cred_rev_creation_time = None

    # Indy create schema response from backchannel
    # {
    #   "<schema_name>": schema_response_json
    # }
    # 
    # context.issuer_schema_dict["Schema_DriversLicense_v2"] = 
    # {
    #   "schema_id": "FSQvDrNnARp3StGUUYYm54:2:test_schema:1.0.0", 
    #   "schema": {
    #       "ver": "1.0", 
    #       "id": "FSQvDrNnARp3StGUUYYm54:2:test_schema:1.0.0", 
    #       "name": "test_schema", 
    #       "version": "1.0.0", 
    #       "attrNames": ["attr_2", "attr_3", "attr_1"],
    #       "seqNo": 10
    #   }
    # }
    context.issuer_schema_dict = {}

    # Indy create credential definition response from backchannel
    # {
    #   "<schema_name>": credential_definition_response_json
    # }
    # 
    # context.issuer_credential_definition_dict["Schema_DriversLicense_v2"] = 
    # {
    #   "ver": "1.0", 
    #   "id": "FSQvDrNnARp3StGUUYYm54:3:CL:10:default", 
    #   "schemaId": "10", 
    #   "type": "CL", 
    #   "tag": "default", 
    #   "value": { ... crypto stuff ... }
    # }
    context.issuer_credential_definition_dict = {}

    # Non revoked time frame
    # {
    #   "non_revoked": {
    #      "from": <int>,
    #      "to": <int>
    #   }
    # }
    # 
    # context.non_revoked = create_non_revoke_interval("-86400:+86400")
    context.non_revoked_timeframe = None

    # Issue credential thread id
    # context.cred_thread_id = "876fc488-c762-41f2-b2b1-dacf461226ef"
    context.cred_thread_id = None

    # Credential revocation id
    # context.cred_rev_id = "ba94c890-8463-40e4-b7f4-0e420fc3bc00"
    context.cred_rev_id = None

    # Credential revocation registry id
    # context.cred_rev_id = "c6d37ebd-a2d9-485f-b393-5fcb86b51fd2"
    context.rev_reg_id = None

    # DIDExchange invitation
    context.responder_invitation = None

    # Get public did response
    # 
    # context.requester_public_did = {
    #   "did": "FSQvDrNnARp3StGUUYYm54"
    #   "verkey": "verkey"
    # }
    context.requester_public_did = None

    # Requester public did
    # 
    # context.requester_did = "FSQvDrNnARp3StGUUYYm54"
    context.requester_did = None

    # Requester public did dod
    # create-request-resolvable did json response
    context.requester_public_did_doc = None

    # Present proof request for proof (presentation proposal object)
    context.request_for_proof = None

    # Whether exchange is connectionless
    context.connectionless = False

    # Presentation exchange id used for connectionless exchanges
    # context.presentation_exchange_id = "6f96b535-0afa-4fff-938a-9f9bd6aa2814"
    context.presentation_exchange_id = None

    # Loaded presentation data
    # 
    # context.presentation = {
    #   "comment": "This is a comment for the send presentation.",
    #   "requested_attributes": {
    #     "health_attrs": {
    #        "cred_type_name": "Schema_Health_ID",
    #        "revealed": true,
    #        "cred_id": "replace_me"
    #     }
    #   }
    # }
    context.presentation = None

    # Presentation exchange thread id
    # 
    # context.presentation_thread_id = "59e17d38-0e90-42bf-93bb-44a42cc716c9"
    context.presentation_thread_id = None

    # Presentation proposal
    # 
    # context.presentation_proposal = {
    #   "requested_attributes": [
    #      {
    #          "name": "address",
    #          "cred_def_id": "replace_me",
    #          "cred_type_name": "Schema_DriversLicense"
    #      }
    #   ]
    # }
    context.presentation_proposal = None

    # Agent name (e.g. Alice, Bob, ...) to connection id mapping (two levels)
    # { 
    #   "<agent_name>": {
    #       "<agent_name>": "<connection_id>"
    #   }
    # }
    # defaultdict allows to instantly set keys without checking:
    # context.connection_id_dict["Alice"]["Bob"] = "4cdc22e4-6563-404b-8245-e8cb407f0abd"
    context.connection_id_dict = defaultdict(dict)

    # ISSUER

    # Schema name to issuer did mapping
    # {
    #   "<schema_name>": "<issuer_did>"
    # }
    # 
    # context.issuer_did_dict["Schema_DriversLicense_v2"] = "FSQvDrNnARp3StGUUYYm54"
    context.issuer_did_dict = {}

    # Indy specific schema name to schema id mapping
    # {
    #   "<schema_name>": "<schema_id>"
    # }
    context.issuer_schema_id_dict = {}

    # Indy specifc schema name to credential definition id mapping
    # {
    #   "<schema_name>": "<credential_definition_id>"
    # } 
    context.credential_definition_id_dict = {}

    # Indy schema name to schema json mapping
    # {
    #   "<schema_name>": <schema_json>
    # }
    # 
    # context.schema_dict["Schema_DriversLicense_v2"] = {
    #   "schema_name":"Schema_DriversLicense_v2",
    #   "schema_version":"1.1.0",
    #   "attributes":[
    #       "address",
    #       "DL_number",
    #       "expiry",
    #       "age"
    #   ]
    # }
    context.schema_dict = {}

    # Presentation Exchange Thread ID to boolean whether the proof is verified mapping
    # {
    #   "<presentation_exchange_thread_id>": <verified_boolean>
    # }
    # 
    # context.credential_verification_dict["515b5850-8d98-4d0b-a1ca-ddd21038db96"] = True
    context.credential_verification_dict = {}

    # Signature suite used for json-ld credentials
    # 
    # context.proof_type = "Ed25519Signature2018"
    context.proof_type = None

    # Did method used for json-ld credentials
    # 
    # context.did_method = "key"
    context.did_method = None
