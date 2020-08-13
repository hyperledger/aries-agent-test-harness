from behave import *
import json
from agent_backchannel_client import agent_backchannel_GET, agent_backchannel_POST, expected_agent_state
from time import sleep

@given('"{prover}" has an issued credential from {issuer} with {credential_data}')
def step_impl(context, prover, issuer, credential_data):
    #assign the credential data to the context for use in the credential offer or proposal. 

    if credential_data != None:
        # Get and assign the data to the context
        # loop as many times as there are schemas and add to the cred data dict based on schema name
        # try:
        #     credential_data_json_file = open('features/data/cred_data_' + context.schema["schema_name"].lower() + '.json')
        #     context.credential_data = json.load(credential_data_json_file)[credential_data]['attributes']
        # except FileNotFoundError:
        #     print(FileNotFoundError + ': features/data/cred_data_' + context.schema["schema_name"].lower() + '.json')

        if "schema_dict" in context:
            for schema in context.schema_dict:
                if 'credential_data_dict' in context:
                    try:
                        credential_data_json_file = open('features/data/cred_data_' + schema.lower() + '.json')
                        context.credential_data_dict[schema] = json.load(credential_data_json_file)[credential_data]['attributes']
                    except FileNotFoundError:
                        print(FileNotFoundError + ': features/data/cred_data_' + schema.lower() + '.json')
                else:
                    try:
                        credential_data_json_file = open('features/data/cred_data_' + schema.lower() + '.json')
                        context.credential_data_dict = {schema: json.load(credential_data_json_file)[credential_data]['attributes']}
                    except FileNotFoundError:
                        print(FileNotFoundError + ': features/data/cred_data_' + schema.lower() + '.json')

        #         context.schema_dict[tag] = schema_json["schema"]
        #         context.support_revocation_dict[tag] = schema_json["cred_def_support_revocation"]
        # else:
        #     context.schema_dict = {tag: schema_json["schema"]}
        #     context.support_revocation_dict = {tag: schema_json["cred_def_support_revocation"]}


    # Call the step below to get the credential issued.
    context.execute_steps('''
        Given "''' + prover + '''" has an issued credential from {issuer}
    '''.format(issuer=issuer))

@given('"{prover}" has an issued credential from {issuer}')
def step_impl(context, prover, issuer):
    # create the Connection between the prover and the issuer
    # TODO: May need to check for an existing connection here instead of creating one.
    context.execute_steps('''
        Given "''' + issuer + '''" and "''' + prover + '''" have an existing connection
    ''')

    # make sure the issuer has the credential definition
    # If there is a schema_dict then we are working with mulitple credential types, loop as many times as 
    # there are schemas and add the schema to context as the issue cred tests expect. 
    if 'schema_dict' not in context:
        context.execute_steps('''
        Given "''' + issuer + '''" has a public did
        When "''' + issuer + '''" creates a new schema
        And "''' + issuer + '''" creates a new credential definition
        Then "''' + issuer + '''" has an existing schema
        And "''' + issuer + '''" has an existing credential definition
        ''')
    else:
        for schema in context.schema_dict:
            context.support_revocation = context.support_revocation_dict[schema]
            context.schema = context.schema_dict[schema]
            context.execute_steps('''
            Given "''' + issuer + '''" has a public did
            When "''' + issuer + '''" creates a new schema
            And "''' + issuer + '''" creates a new credential definition
            Then "''' + issuer + '''" has an existing schema
            And "''' + issuer + '''" has an existing credential definition
            ''')

    # setup the holder and issuer for the issue cred sceneario below. The data table in the tests does not setup a holder.
    # The prover is also the holder.
    context.holder_url = context.config.userdata.get(prover)
    context.holder_name = prover
    assert context.holder_url is not None and 0 < len(context.holder_url)
    # The issuer was not in the data table, it was in the gherkin scenario outline examples, so get it and assign it.
    context.issuer_url = context.config.userdata.get(issuer)
    context.issuer_name = issuer
    assert context.issuer_url is not None and 0 < len(context.issuer_url)

    # issue the credential to prover
    # If there is a schema_dict then we are working with mulitple credential types, loop as many times as 
    # there are schemas and add the schema to context as the issue cred tests expect. 
    if 'schema_dict' not in context:
        context.execute_steps('''
            When  "''' + prover + '''" proposes a credential to "''' + issuer + '''"
            And  "''' + issuer + '''" offers a credential
            And "''' + prover + '''" requests the credential
            And  "''' + issuer + '''" issues the credential
            And "''' + prover + '''" acknowledges the credential issue
            Then "''' + prover + '''" has the credential issued
        ''')
    else:
        for schema in context.schema_dict:
            context.credential_data = context.credential_data_dict[schema]
            context.schema = context.schema_dict[schema]
            context.execute_steps('''
                When  "''' + prover + '''" proposes a credential to "''' + issuer + '''"
                And  "''' + issuer + '''" offers a credential
                And "''' + prover + '''" requests the credential
                And  "''' + issuer + '''" issues the credential
                And "''' + prover + '''" acknowledges the credential issue
                Then "''' + prover + '''" has the credential issued
            ''')
    

@when('"{verifier}" sends a request for proof presentation to "{prover}"')
def step_impl(context, verifier, prover):

    # check for a schema template already loaded in the context. If it is, it was loaded from an external Schema, so use it.
    if "request_for_proof" in context:
        data = context.request_for_proof
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

    if ('connectionless' in context) and (context.connectionless == True):
        presentation_proposal = {
            "presentation_proposal": {
                "@type": "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/present-proof/1.0/request-presentation",
                "comment": "This is a comment for the request for presentation.",
                "request_presentations~attach": {
                    "@id": "libindy-request-presentation-0",
                    "mime-type": "application/json",
                    "data":  data
                }
            }
        }
        (resp_status, resp_text) = agent_backchannel_POST(context.verifier_url + "/agent/command/", "proof", operation="create-send-connectionless-request", data=presentation_proposal)
    else:
        presentation_proposal = {
            "connection_id": context.connection_id_dict[verifier][prover],
            "presentation_proposal": {
                "@type": "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/present-proof/1.0/request-presentation",
                "comment": "This is a comment for the request for presentation.",
                "request_presentations~attach": {
                    "@id": "libindy-request-presentation-0",
                    "mime-type": "application/json",
                    "data":  data
                }
            }
        }

    if ('connectionless' in context) and (context.connectionless == True):
        resp_json = json.loads(resp_text)

        presentation_proposal["~service"] = {
                "recipientKeys": [
                    resp_json["presentation_exchange_id"]
                ],
                "routingKeys": None,
                "serviceEndpoint": context.verifier_url
                }


    # send presentation request
    (resp_status, resp_text) = agent_backchannel_POST(context.verifier_url + "/agent/command/", "proof", operation="send-request", data=presentation_proposal)
    
    assert resp_status == 200, f'resp_status {resp_status} is not 200; {resp_text}'
    resp_json = json.loads(resp_text)
    # check the state of the presentation from the verifiers perspective
    assert resp_json["state"] == "request-sent"

    # save off anything that is returned in the response to use later?
    context.presentation_thread_id = resp_json["thread_id"]

    # check the state of the presentation from the provers perspective
    # if the protocol is connectionless then don't do this, the prover has not recieved anything yet.
    if ('connectionless' not in context) or (context.connectionless == False):
        assert expected_agent_state(context.prover_url, "proof", context.presentation_thread_id, "request-received")
    else:
        # save off the presentation exchange id for use when the prover sends the presentation with a service decorator
        context.presentation_exchange_id = resp_json["presentation_exchange_id"]

@when('"{verifier}" sends a {request_for_proof} presentation to "{prover}"')
def step_impl(context, verifier, request_for_proof, prover):
    try:
        request_for_proof_json_file = open('features/data/' + request_for_proof + '.json')
        request_for_proof_json = json.load(request_for_proof_json_file)
        context.request_for_proof = request_for_proof_json["presentation_proposal"]

    except FileNotFoundError:
        print(FileNotFoundError + ': features/data/' + request_for_proof + '.json')

    # Call the step below to get send rhe request for presentation.
    context.execute_steps('''
        When "''' + verifier + '''" sends a request for proof presentation to "''' + prover + '''"
    ''')

@when('"{prover}" makes the presentation of the proof')
def step_impl(context, prover):
    prover_url = context.prover_url

    if "presentation" in context:
        presentation = context.presentation
        # Find the cred ids and add the actual cred id into the presentation
        # TODO: There is probably a better way to get access to the specific requested attributes and predicates. Revisit this later.
        try:
            for i in range(json.dumps(presentation["requested_attributes"]).count("cred_id")):
                # Get the schema name from the loaded presentation for each requested attributes
                cred_type_name = presentation["requested_attributes"][list(presentation["requested_attributes"])[i]]["cred_type_name"]
                presentation["requested_attributes"][list(presentation["requested_attributes"])[i]]["cred_id"] = context.credential_id_dict[cred_type_name]
                # Remove the cred_type_name from this part of the presentation since it won't be needed in the actual request.
                presentation["requested_attributes"][list(presentation["requested_attributes"])[i]].pop("cred_type_name")
        except KeyError:
            pass
        
        try:
            for i in range(json.dumps(presentation["requested_predicates"]).count("cred_id")):
                # Get the schema name from the loaded presentation for each requested predicates
                cred_type_name = presentation["requested_predicates"][list(presentation["requested_predicates"])[i]]["cred_type_name"]
                presentation["requested_predicates"][list(presentation["requested_predicates"])[i]]["cred_id"] = context.credential_id_dict[cred_type_name] 
                # Remove the cred_type_name from this part of the presentation since it won't be needed in the actual request.
                presentation["requested_predicates"][list(presentation["requested_predicates"])[i]].pop("cred_type_name")
        except KeyError:
            pass

    else:   
        presentation = {
            "comment": "This is a comment for the send presentation.",
            "requested_attributes": {
                "attr_1": {
                    "revealed": True,
                    "cred_id": context.credential_id_dict[context.schema['schema_name']]
                }
            }
        }

    # if this is happening connectionless, then add the service decorator to the presentation
    if ('connectionless' in context) and (context.connectionless == True):
        presentation["~service"] = {
                "recipientKeys": [
                    context.presentation_exchange_id
                ],
                "routingKeys": None,
                "serviceEndpoint": context.verifier_url
            }

    (resp_status, resp_text) = agent_backchannel_POST(prover_url + "/agent/command/", "proof", operation="send-presentation", id=context.presentation_thread_id, data=presentation)
    assert resp_status == 200, f'resp_status {resp_status} is not 200; {resp_text}'
    resp_json = json.loads(resp_text)
    assert resp_json["state"] == "presentation-sent"

    # check the state of the presentation from the verifier's perspective
    assert expected_agent_state(context.verifier_url, "proof", context.presentation_thread_id, "presentation-received")

@when('"{prover}" makes the {presentation} of the proof')
def step_impl(context, prover, presentation):
    try:
        presentation_json_file = open('features/data/' + presentation + '.json')
        presentation_json = json.load(presentation_json_file)
        context.presentation = presentation_json["presentation"]

    except FileNotFoundError:
        print(FileNotFoundError + ': features/data/' + presentation + '.json')

    # Call the step below to get send rhe request for presentation.
    context.execute_steps('''
        When "''' + prover + '''" makes the presentation of the proof
    ''')

@when('"{verifier}" acknowledges the proof')
def step_impl(context, verifier):
    verifier_url = context.verifier_url

    (resp_status, resp_text) = agent_backchannel_POST(verifier_url + "/agent/command/", "proof", operation="verify-presentation", id=context.presentation_thread_id)
    assert resp_status == 200, f'resp_status {resp_status} is not 200; {resp_text}'
    resp_json = json.loads(resp_text)
    assert resp_json["state"] == "done"

@then('"{prover}" has the proof acknowledged')
def step_impl(context, prover):
    # check the state of the presentation from the prover's perspective
    assert expected_agent_state(context.prover_url, "proof", context.presentation_thread_id, "done")

@given('"{verifier}" and "{prover}" do not have a connection')
def step_impl(context, verifier, prover):
    context.connectionless = True

@when('"{prover}" doesn’t want to reveal what was requested so makes a presentation proposal')
def step_impl(context, prover):
   
    # check for a schema template already loaded in the context. If it is, it was loaded from an external Schema, so use it.
    if "request_for_proof" in context:
        data = context.request_for_proof
    else:   
        data = {
                    "requested_values": {
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

    if ('connectionless' in context) and (context.connectionless == True):
        presentation_proposal = {
            "presentation_proposal": {
                "@type": "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/present-proof/1.0/request-presentation",
                "comment": "This is a comment for the request for presentation.",
                "request_presentations~attach": {
                    "@id": "libindy-request-presentation-0",
                    "mime-type": "application/json",
                    "data": data
                }
            }
        }
    else:
        presentation_proposal = {
            "connection_id": context.connection_id_dict[prover][context.verifier_name],
            "presentation_proposal": {
                "@type": "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/present-proof/1.0/request-presentation",
                "comment": "This is a comment for the request for presentation.",
                "request_presentations~attach": {
                    "@id": "libindy-request-presentation-0",
                    "mime-type": "application/json",
                    "data": data
                }
            }
        }

        

    # send presentation proposal
    (resp_status, resp_text) = agent_backchannel_POST(context.prover_url + "/agent/command/", "proof", operation="send-proposal", data=presentation_proposal)
    assert resp_status == 200, f'resp_status {resp_status} is not 200; {resp_text}'
    resp_json = json.loads(resp_text)
    # check the state of the presentation from the verifiers perspective
    assert resp_json["state"] == "proposal-sent"

    # save off anything that is returned in the response to use later?
    context.presentation_thread_id = resp_json["thread_id"]

    # check the state of the presentation from the provers perspective
    assert expected_agent_state(context.verifier_url, "proof", context.presentation_thread_id, "proposal-received")


@when(u'"{verifier}" agrees to continue so sends a request for proof presentation')
def step_impl(context, verifier):
    # send presentation request
    (resp_status, resp_text) = agent_backchannel_POST(context.verifier_url + "/agent/command/", "proof", operation="send-request", id=context.presentation_thread_id, data=presentation_proposal)
    assert resp_status == 200, f'resp_status {resp_status} is not 200; {resp_text}'
    resp_json = json.loads(resp_text)
    # check the state of the presentation from the verifiers perspective
    assert resp_json["state"] == "request-sent"

    # save off anything that is returned in the response to use later?
    context.presentation_thread_id = resp_json["thread_id"]

    # check the state of the presentation from the provers perspective
    assert expected_agent_state(context.prover_url, "proof", context.presentation_thread_id, "request-received")
    #assert present_proof_status(context.prover_url, context.presentation_thread_id, "request-received")