from behave import *
import json
from agent_backchannel_client import agent_backchannel_POST, expected_agent_state
from agent_test_utils import get_relative_timestamp_to_epoch
from time import sleep

@when('{issuer} issues a new credential to "{prover}" with {credential_data}')
@given('"{prover}" has an issued credential from {issuer} with {credential_data}')
def step_impl(context, prover, issuer, credential_data):
    # assign the credential data to the context for use in the credential offer or proposal. 
    if credential_data != None:
        for schema_name in context.schema_dict:
            try:
                credential_data_json_file = open('features/data/cred_data_' + schema_name.lower() + '.json')
                context.credential_data_dict[schema_name] = json.load(credential_data_json_file)[credential_data]['attributes']
            except FileNotFoundError:
                print(FileNotFoundError + ': features/data/cred_data_' + schema_name.lower() + '.json')


    # Call the step below to get the credential issued.
    context.execute_steps(f'''
        Given "{prover}" has an issued credential from {issuer}
    ''')

@given('"{prover}" has an issued credential from {issuer}')
def step_impl(context, prover, issuer):
    # create the Connection between the prover and the issuer
    # TODO: May need to check for an existing connection established from other tests here instead of creating one.
    # Check if a connection between the players has already been established in this test. 
    if prover not in context.connection_id_dict or issuer not in context.connection_id_dict[prover]:
        context.execute_steps(f'''
            Given "{issuer}" and "{prover}" have an existing connection
        ''')


    # make sure the issuer has the credential definition
    # If schema dict has keys we ware working with multiple credential types, loop as many times as 
    # there are schemas and add the schema to context as the issue cred tests expect. 
    if len(context.schema_dict) == 0:
        context.execute_steps(f'''
           Given "{issuer}" has a public did
            When "{issuer}" creates a new schema
             And "{issuer}" creates a new credential definition
            Then "{issuer}" has an existing schema
             And "{issuer}" has an existing credential definition
        ''')
    else:
        for schema in context.schema_dict:
            context.support_revocation = context.support_revocation_dict[schema]
            context.schema = context.schema_dict[schema]
            context.execute_steps(f'''
               Given "{issuer}" has a public did
                When "{issuer}" creates a new schema
                 And "{issuer}" creates a new credential definition
                Then "{issuer}" has an existing schema
                 And "{issuer}" has an existing credential definition
            ''')

    # setup the holder and issuer for the issue cred scenario below. The data table in the tests does not setup a holder.
    # The prover is also the holder.
    context.holder_url = context.config.userdata.get(prover)
    context.holder_name = prover
    assert context.holder_url is not None and 0 < len(context.holder_url)
    # The issuer was not in the data table, it was in the gherkin scenario outline examples, so get it and assign it.
    context.issuer_url = context.config.userdata.get(issuer)
    context.issuer_name = issuer
    assert context.issuer_url is not None and 0 < len(context.issuer_url)

    # issue the credential to prover
    # If there is a schema_dict then we are working with multiple credential types, loop as many times as 
    # there are schemas and add the schema to context as the issue cred tests expect. 
    if len(context.schema_dict) == 0:
        context_steps = f'''
            When "{issuer}" offers a credential
            And "{prover}" requests the credential
            And  "{issuer}" issues the credential
            And "{prover}" acknowledges the credential issue
            Then "{prover}" has the credential issued
        '''
        context.execute_steps(context_steps)
    else:
        for schema in context.schema_dict:
            context.credential_data = context.credential_data_dict[schema]
            context.schema = context.schema_dict[schema]
            context_steps = f'''
                When "{issuer}" offers a credential
                And "{prover}" requests the credential
                And  "{issuer}" issues the credential
                And "{prover}" acknowledges the credential issue
                Then "{prover}" has the credential issued
            '''
            context.execute_steps(context_steps)
    

@when('"{verifier}" sends a request for proof presentation to "{prover}"')
def step_impl(context, verifier, prover):

    # check for a schema template already loaded in the context. If it is, it was loaded from an external Schema, so use it.
    if context.request_for_proof:
        data = context.request_for_proof

        if context.non_revoked_timeframe:
             data["non_revoked"] = context.non_revoked_timeframe["non_revoked"]
    else:   
        data = {
                    "requested_attributes": {
                        "attr_1": {
                            "name": "attr_1",
                            "restrictions": [
                                {
                                    "schema_name": "test_schema." + context.issuer_name,
                                    "schema_version": "1.0.0"
                                }
                            ]
                        }
                    }
                }

    presentation_request = {
        "presentation_request": {
            "comment": "This is a comment for the request for presentation.",
            "proof_request": {
                "data":  data
            }
        }
    }


    if context.connectionless:
        (resp_status, resp_text) = agent_backchannel_POST(context.verifier_url + "/agent/command/", "proof", operation="create-send-connectionless-request", data=presentation_request)       
    else:
        presentation_request["connection_id"] = context.connection_id_dict[verifier][prover]

        # send presentation request
        (resp_status, resp_text) = agent_backchannel_POST(context.verifier_url + "/agent/command/", "proof", operation="send-request", data=presentation_request)
    
    assert resp_status == 200, f'resp_status {resp_status} is not 200; {resp_text}'
    resp_json = json.loads(resp_text)
    # check the state of the presentation from the verifiers perspective
    #assert resp_json["state"] == "request-sent"

    # save off anything that is returned in the response to use later?
    context.presentation_thread_id = resp_json["thread_id"]


    if context.connectionless:
        # save off the presentation exchange id for use when the prover sends the presentation with a service decorator
        context.presentation_exchange_id = resp_json["presentation_exchange_id"]
    else:
        # TODO Removing this line causes too many failures in Acapy-Dotnet Acapy-Afgo. 
        assert expected_agent_state(context.prover_url, "proof", context.presentation_thread_id, "request-received")

@when('"{verifier}" agrees with the proposal so sends a {request_for_proof} presentation to "{prover}"')
@when('"{verifier}" sends a {request_for_proof} presentation to "{prover}"')
def step_impl(context, verifier, request_for_proof, prover):
    try:
        request_for_proof_json_file = open('features/data/' + request_for_proof + '.json')
        request_for_proof_json = json.load(request_for_proof_json_file)
        context.request_for_proof = request_for_proof_json["presentation_request"]

    except FileNotFoundError:
        print(FileNotFoundError + ': features/data/' + request_for_proof + '.json')

    # Call the step below to get send rhe request for presentation.
    context.execute_steps(f'''
        When "{verifier}" sends a request for proof presentation to "{prover}"
    ''')

@when('"{prover}" makes the presentation of the proof')
def step_impl(context, prover):
    prover_url = context.prover_url

    if context.presentation:
        presentation = context.presentation
        # Find the cred ids and add the actual cred id into the presentation
        # TODO: There is probably a better way to get access to the specific requested attributes and predicates. Revisit this later.
        try:
            for requested_attribute in presentation["requested_attributes"].values():
                # Get the schema name from the loaded presentation for each requested attributes
                cred_type_name = requested_attribute["cred_type_name"]
                requested_attribute["cred_id"] = context.credential_id_dict[cred_type_name][-1]
                
                # If there is a timestamp, calculate it from the instruction in the file. Can be 'now' or + - relative to now.
                if "timestamp" in requested_attribute:
                    relative_timestamp = requested_attribute["timestamp"]
                    requested_attribute["timestamp"] = get_relative_timestamp_to_epoch(relative_timestamp)
                
                # Remove the cred_type_name from this part of the presentation since it won't be needed in the actual request.
                requested_attribute.pop("cred_type_name")
        except KeyError:
            pass
        
        try:
            for requested_predicate in presentation["requested_predicates"].values():
                # Get the schema name from the loaded presentation for each requested predicates
                cred_type_name = requested_predicate["cred_type_name"]
                requested_predicate["cred_id"] = context.credential_id_dict[cred_type_name][-1]
                
                # If there is a timestamp, calculate it from the instruction in the file. Can be 'now' or + - relative to now.
                if "timestamp" in requested_predicate:
                    relative_timestamp = requested_predicate["timestamp"]
                    requested_predicate["timestamp"] = get_relative_timestamp_to_epoch(relative_timestamp)
                
                # Remove the cred_type_name from this part of the presentation since it won't be needed in the actual request.
                requested_predicate.pop("cred_type_name")
        except KeyError:
            pass

    else:   
        presentation = {
            "comment": "This is a comment for the send presentation.",
            "requested_attributes": {
                "attr_1": {
                    "revealed": True,
                    "cred_id": context.credential_id_dict[context.schema['schema_name']][-1]
                }
            }
        }

    # if this is happening connectionless, then add the service decorator to the presentation
    if context.connectionless:
        presentation["~service"] = {
                "recipientKeys": [
                    context.presentation_exchange_id
                ],
                "routingKeys": None,
                "serviceEndpoint": context.verifier_url
            }

    (resp_status, resp_text) = agent_backchannel_POST(prover_url + "/agent/command/", "proof", operation="send-presentation", id=context.presentation_thread_id, data=presentation)
    assert resp_status == 200, f'resp_status {resp_status} is not 200; {resp_text}'


@when('"{prover}" makes the {presentation} of the proof')
def step_impl(context, prover, presentation):
    try:
        presentation_json_file = open('features/data/' + presentation + '.json')
        presentation_json = json.load(presentation_json_file)
        context.presentation = presentation_json["presentation"]

    except FileNotFoundError:
        print(FileNotFoundError + ': features/data/' + presentation + '.json')

    # Call the step below to get send rhe request for presentation.
    context.execute_steps(f'''
        When "{prover}" makes the presentation of the proof
    ''')

@when('"{verifier}" acknowledges the proof')
def step_impl(context, verifier):
    verifier_url = context.verifier_url

    sleep(3)
    (resp_status, resp_text) = agent_backchannel_POST(verifier_url + "/agent/command/", "proof", operation="verify-presentation", id=context.presentation_thread_id)
    assert resp_status == 200, f'resp_status {resp_status} is not 200; {resp_text}'
    resp_json = json.loads(resp_text)
    assert resp_json["state"] == "done"

    # FIXME: why do we only store the verified property if support_revocation is enabled?
    if context.support_revocation:
        verified = resp_json["verified"] == True or resp_json["verified"] == "true"
        context.credential_verification_dict[context.presentation_thread_id] = verified

@then('"{prover}" has the proof verified')
def step_impl(context, prover):
    # check the state of the presentation from the prover's perspective
    assert expected_agent_state(context.prover_url, "proof", context.presentation_thread_id, "done", wait_time=10.0)

    if context.presentation_thread_id in context.credential_verification_dict:
        # Check the status of the verification in the verify-presentation call. Should be True
        assert context.credential_verification_dict[context.presentation_thread_id]

@given('"{verifier}" and "{prover}" do not have a connection')
def step_impl(context, verifier, prover):
    context.connectionless = True

@when('"{prover}" doesn’t want to reveal what was requested so makes a presentation proposal')
def step_impl(context, prover):
   
    # check for a schema template already loaded in the context. If it is, it was loaded from an external Schema, so use it.
    if context.presentation_proposal:
        data = context.presentation_proposal
    else:   
        data = {
            "attributes": [
                {
                    "name": "attr_2",
                    "cred_def_id": context.credential_definition_id_dict[context.schema["schema_name"]],
                }
            ]
        }

    attributes = data.get("attributes") or []
    predicates = data.get("predicates") or []

    presentation_proposal = {
        "presentation_proposal": {
            "comment": "This is a comment for the presentation proposal.",
            "attributes": attributes,
            "predicates": predicates
        }
    }

    if not context.connectionless:
        presentation_proposal["connection_id"] = context.connection_id_dict[prover][context.verifier_name]

    # send presentation proposal
    (resp_status, resp_text) = agent_backchannel_POST(context.prover_url + "/agent/command/", "proof", operation="send-proposal", data=presentation_proposal)
    assert resp_status == 200, f'resp_status {resp_status} is not 200; {resp_text}'
    resp_json = json.loads(resp_text)

    # save off anything that is returned in the response to use later?
    context.presentation_thread_id = resp_json["thread_id"]


@when(u'"{verifier}" agrees to continue so sends a request for proof presentation')
def step_impl(context, verifier):
    # Construct the presentation request from the presention proposal.
    # This should be removed in V2.0 since data is not required with a thread id.
    data = {
        "requested_attributes": {
            "attr_2": {
                "name": "attr_2",
                "restrictions": [
                    {
                        "schema_name": "test_schema." + context.issuer_name,
                        "schema_version": "1.0.0"
                    }
                ]
            }
        }
    }
    presentation_request = {
        "presentation_request": {
            "comment": "This is a comment for the request for presentation.",
            "proof_request": {
                "data":  data
            }
        }
    }
    
    if not context.connectionloess:
        presentation_request["connection_id"] = context.connection_id_dict[verifier][context.prover_name]
    
    # send presentation request
    (resp_status, resp_text) = agent_backchannel_POST(context.verifier_url + "/agent/command/", "proof", operation="send-request", id=context.presentation_thread_id, data=presentation_request)
    
    assert resp_status == 200, f'resp_status {resp_status} is not 200; {resp_text}'
    resp_json = json.loads(resp_text)


@when('"{prover}" doesn’t want to reveal what was requested so makes a {proposal}')
@when('"{prover}" makes a {proposal} to "{verifier}"')
def step_impl(context, prover, proposal, verifier=None):
    try:
        proposal_json_file = open('features/data/' + proposal + '.json')
        proposal_json = json.load(proposal_json_file)
        context.presentation_proposal = proposal_json["presentation_proposal"]

        # replace the cred_def_id with the actual id based on the cred type name
        try:
            for requested_attribute in context.presentation_proposal["attributes"]:
                # Get the cred type name from the loaded presentation for each requested attributes
                cred_type_name = requested_attribute["cred_type_name"]
                requested_attribute["cred_def_id"] = context.credential_definition_id_dict[cred_type_name]

                # Remove the cred_type_name from this part of the presentation since it won't be needed in the actual request.
                requested_attribute.pop("cred_type_name")
        except KeyError:
            pass
        
        try:
            for requested_predicate in context.presentation_proposal["predicates"]:
                 # Get the schema name from the loaded presentation for each requested predicates
                cred_type_name = requested_predicate["cred_type_name"]
                requested_predicate["cred_def_id"] = context.credential_definition_id_dict[cred_type_name] 

                # Remove the cred_type_name from this part of the presentation since it won't be needed in the actual request.
                requested_predicate.pop("cred_type_name")
        except KeyError:
            pass

    except FileNotFoundError:
        print(FileNotFoundError + ': features/data/' + proposal + '.json')

    # Call the existing proposal step to make the proposal.
    context.execute_steps(f'''
        When "{prover}" doesn’t want to reveal what was requested so makes a presentation proposal
    ''')


#
# Step Definitions to complete the presentation rejection test scenario - T005-AIP10-RFC0037
#
@when(u'"{prover}" makes the {presentation} of the proof incorrectly so "{verifier}" rejects the proof')
def step_impl(context, prover, presentation, verifier):
    try:
        presentation_json_file = open('features/data/' + presentation + '.json')
        presentation_json = json.load(presentation_json_file)
        context.presentation = presentation_json["presentation"]

    except FileNotFoundError:
        print(FileNotFoundError + ': features/data/' + presentation + '.json')

    presentation = context.presentation
    # FIXME: why is this commented?
    # Find the cred ids and add the actual cred id into the presentation
    # try:
    #     for i in range(json.dumps(presentation["requested_attributes"]).count("cred_id")):
    #         # Get the schema name from the loaded presentation for each requested attributes
    #         cred_type_name = presentation["requested_attributes"][list(presentation["requested_attributes"])[i]]["cred_type_name"]
    #         #presentation["requested_attributes"][list(presentation["requested_attributes"])[i]]["cred_id"] = context.credential_id_dict[cred_type_name]
    #         presentation["requested_predicates"][list(presentation["requested_predicates"])[i]]["cred_id"] = '0' 
    #         # Remove the cred_type_name from this part of the presentation since it won't be needed in the actual request.
    #         presentation["requested_attributes"][list(presentation["requested_attributes"])[i]].pop("cred_type_name")
    # except KeyError:
    #     pass
    
    # try:
    #     for i in range(json.dumps(presentation["requested_predicates"]).count("cred_id")):
    #         # Get the schema name from the loaded presentation for each requested predicates
    #         cred_type_name = presentation["requested_predicates"][list(presentation["requested_predicates"])[i]]["cred_type_name"]
    #         #presentation["requested_predicates"][list(presentation["requested_predicates"])[i]]["cred_id"] = context.credential_id_dict[cred_type_name]
    #         presentation["requested_predicates"][list(presentation["requested_predicates"])[i]]["cred_id"] = '1' 
    #         # Remove the cred_type_name from this part of the presentation since it won't be needed in the actual request.
    #         presentation["requested_predicates"][list(presentation["requested_predicates"])[i]].pop("cred_type_name")
    # except KeyError:
    #     pass

    # Change something in the presentation data to cause a problem report


    (resp_status, resp_text) = agent_backchannel_POST(context.prover_url + "/agent/command/", "proof", operation="send-presentation", id=context.presentation_thread_id, data=presentation)
    assert resp_status == 400, f'resp_status {resp_status} is not 400; {resp_text}'



# FIXME: why is this commented?
# @when(u'"{verifier}" rejects the proof so sends a presentation rejection')
# def step_impl(context, verifier):
#     pass
#     #raise NotImplementedError(u'STEP: When "Faber" rejects the proof so sends a presentation rejection')

@then(u'"{prover}" has the proof unverified')
def step_impl(context, prover):
    # check the state of the presentation from the prover's perspective
    # in the unacknowledged case, the state of the prover is still done. There probably should be something else to check.
    # like having the verified: false in the response. Change this if agents start to report the verified state. 
    assert expected_agent_state(context.prover_url, "proof", context.presentation_thread_id, "done")

    if context.credential_verification_dict:
        # Check the status of the verification in the verify-presentation call. Should be False
        assert not context.credential_verification_dict[context.presentation_thread_id]