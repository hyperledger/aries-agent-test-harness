# -----------------------------------------------------------
# Behave Step Definitions for Credential Revocation 0011 and Revocation Notification Protocol 0183
# used to revoke issued credentials.
#
# GitHub Issue(s) for Test Development:
# https://app.zenhub.com/workspaces/von---verifiable-organization-network-5adf53987ccbaa70597dbec0/issues/hyperledger/aries-agent-test-harness/102
#
# 0011 Revocation RFC: 
# https://github.com/hyperledger/aries-rfcs/tree/9b0aaa39df7e8bd434126c4b33c097aae78d65bf/features/0160-connection-protocol#0160-connection-protocol
#
# 0183 Revocation Notification RFC:
# https://github.com/hyperledger/aries-rfcs/tree/master/features/0183-revocation-notification
#
# Current AIP version level of test coverage: N/A - Revocation is not apart of any AIP Version
#  
# -----------------------------------------------------------

from behave import *
import json
from time import sleep
from agent_backchannel_client import agent_backchannel_GET, agent_backchannel_POST, agent_backchannel_DELETE#, expected_agent_state
from agent_test_utils import create_non_revoke_interval

@when('{issuer} revokes the credential')
def step_impl(context, issuer):

    issuer_url = context.config.userdata.get(issuer)

    credential_revocation = {
        "cred_rev_id": context.cred_rev_id,
        "rev_registry_id": context.rev_reg_id,
        "publish_immediately": True,
    }

    (resp_status, resp_text) = agent_backchannel_POST(issuer_url + "/agent/command/", "revocation", operation="revoke", data=credential_revocation)
    assert resp_status == 200, f'resp_status {resp_status} is not 200; {resp_text}'
    # resp_json = json.loads(resp_text)

    # Check the Holder wallet for the credential
    # Should be a 200 since the revoke doesn't remove the cred from the holders wallet. 
    # What else to check?
    (resp_status, resp_text) = agent_backchannel_GET(context.config.userdata.get(context.holder_name) + "/agent/command/", "credential", id=context.credential_id_dict[context.schema['schema_name']][len(context.credential_id_dict[context.schema['schema_name']])-1])
    assert resp_status == 200, f'resp_status {resp_status} is not 200; {resp_text}'

    # if this is ACA-py then there is provision for the holder to check the revocation status of the cred then they can take action,
    # like delete it from their wallet. This should be done, since the algorithm that 
    if "delete_cred_from_wallet" in context.tags:
        # Call the revocation status api
        #(resp_status, resp_text) = agent_backchannel_GET(context.prover_url + "/agent/command/", "revocation", operation="credential-record", data=credential_revocation)
        (resp_status, resp_text) = agent_backchannel_GET(context.prover_url + "/agent/command/", "credential", operation="revoked", id=context.credential_id_dict[context.schema['schema_name']][len(context.credential_id_dict[context.schema['schema_name']])-1])
        assert resp_status == 200, f'resp_status {resp_status} is not 200; {resp_text}'
        # get the credential status verified out of the response
        # Could also add the cred status to the cred id dict. Maybe later if needed.
        resp_json = json.loads(resp_text)
        revoked = resp_json["revoked"]
        if revoked == True:
            # Call the delete on the credential in the wallet 
            (resp_status, resp_text) = agent_backchannel_DELETE(context.prover_url + "/agent/command/", "credential", id=context.credential_id_dict[context.schema['schema_name']][len(context.credential_id_dict[context.schema['schema_name']])-1])
            assert resp_status == 200, f'resp_status {resp_status} is not 200; {resp_text}'


@when('"{prover}" makes the {presentation} of the proof with the revoked credential')
def step_impl(context, prover, presentation):
    # Swap previous cred ID that was revoked with current in the credential id dict. 
    context.credential_id_dict[context.schema['schema_name']].reverse()

    # Call prover makes the presentation of the proof
    context.execute_steps(f'''
        When "{prover}" makes the {presentation} of the proof
    ''')

@given('{issuer} has revoked the credential after {timeframe}')
@given('{issuer} has revoked the credential before {timeframe}')
@given('{issuer} has revoked the credential within {timeframe}')
def step_impl(context, issuer, timeframe):
    # keeping this step here just in case there is a reason to use the timframe here instead of just the request for proof.

    # context.execute_steps(u'''
    #     When "''' + issuer + '''" revokes the credential
    #  ''')
    context.execute_steps(f'''
        When {issuer} revokes the credential
     ''')

@when('"{verifier}" sends a {request_for_proof} presentation to "{prover}" with credential validity after {timeframe}')
@when('"{verifier}" sends a {request_for_proof} presentation to "{prover}" with credential validity before {timeframe}')
@when('"{verifier}" sends a {request_for_proof} presentation to "{prover}" with credential validity during {timeframe}')
def step_impl(context, verifier, request_for_proof, prover, timeframe):
    
    # Sleep here just to give a little space between the revocation and the request.
    sleep(2)
    context.non_revoked_timeframe = create_non_revoke_interval(timeframe)

    context.execute_steps(f'''
        When "{verifier}" sends a {request_for_proof} presentation to "{prover}"
    ''')

