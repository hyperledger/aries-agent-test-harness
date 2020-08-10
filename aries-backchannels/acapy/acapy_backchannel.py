import asyncio
import asyncpg
import functools
import json
import logging
import os
import random
import subprocess
import sys
import uuid
from timeit import default_timer
from time import sleep
from operator import itemgetter

from aiohttp import (
    web,
    ClientSession,
    ClientRequest,
    ClientResponse,
    ClientError,
    ClientTimeout,
)

from python.agent_backchannel import AgentBackchannel, default_genesis_txns, RUN_MODE, START_TIMEOUT
from python.utils import require_indy, flatten, log_json, log_msg, log_timer, output_reader, prompt_loop
from python.storage import store_resource, get_resource, delete_resource, push_resource, pop_resource

#from helpers.jsonmapper.json_mapper import JsonMapper

LOGGER = logging.getLogger(__name__)

MAX_TIMEOUT = 5

DEFAULT_BIN_PATH = "../venv/bin"
DEFAULT_PYTHON_PATH = ".."

if RUN_MODE == "docker":
    DEFAULT_BIN_PATH = "./bin"
    DEFAULT_PYTHON_PATH = "."
elif RUN_MODE == "pwd":
    DEFAULT_BIN_PATH = "./bin"
    DEFAULT_PYTHON_PATH = "."

class AcaPyAgentBackchannel(AgentBackchannel):
    def __init__(
        self, 
        ident: str,
        http_port: int,
        admin_port: int,
        genesis_data: str = None,
        params: dict = {}
    ):
        super().__init__(
            ident,
            http_port,
            admin_port,
            genesis_data,
            params
        )

        # Aca-py : RFC
        self.connectionStateTranslationDict = {
            "invitation": "invited",
            "request": "requested",
            "response": "responded",
            "active": "complete"
        }

        # Aca-py : RFC
        self.issueCredentialStateTranslationDict = {
            "proposal_sent": "proposal-sent",
            "proposal_received": "proposal-received",
            "offer_sent": "offer-sent",
            "offer_received": "offer-received",
            "request_sent": "request-sent",
            "request_received": "request-received",
            "credential_issued": "credential-issued",
            "credential_received": "credential-received",
            "credential_acked": "done"
        }

        # Aca-py : RFC
        self.presentProofStateTranslationDict = {
            "request_sent": "request-sent",
            "request_received": "request-received",
            "proposal_sent": "proposal-sent",
            "proposal_received": "proposal_received",
            "presentation_sent": "presentation-sent",
            "presentation_received": "presentation-received",
            "reject_sent": "reject-sent",
            "verified": "done",
            "presentation_acked": "done"
        }

    def get_agent_args(self):
        result = [
            ("--endpoint", self.endpoint),
            ("--label", self.label),
            #"--auto-ping-connection",
            #"--auto-accept-invites", 
            #"--auto-accept-requests", 
            #"--auto-respond-messages",
            ("--inbound-transport", "http", "0.0.0.0", str(self.http_port)),
            ("--outbound-transport", "http"),
            ("--admin", "0.0.0.0", str(self.admin_port)),
            "--admin-insecure-mode",
            ("--wallet-type", self.wallet_type),
            ("--wallet-name", self.wallet_name),
            ("--wallet-key", self.wallet_key),
        ]
        if self.genesis_data:
            result.append(("--genesis-transactions", self.genesis_data))
        if self.seed:
            result.append(("--seed", self.seed))
        if self.storage_type:
            result.append(("--storage-type", self.storage_type))
        if self.postgres:
            result.extend(
                [
                    ("--wallet-storage-type", "postgres_storage"),
                    ("--wallet-storage-config", json.dumps(self.postgres_config)),
                    ("--wallet-storage-creds", json.dumps(self.postgres_creds)),
                ]
            )
        if self.webhook_url:
            result.append(("--webhook-url", self.webhook_url))
        #if self.extra_args:
        #    result.extend(self.extra_args)

        return result

    async def listen_webhooks(self, webhook_port):
        self.webhook_port = webhook_port
        if RUN_MODE == "pwd":
            self.webhook_url = f"http://localhost:{str(webhook_port)}/webhooks"
        else:
            self.webhook_url = (
                f"http://{self.external_host}:{str(webhook_port)}/webhooks"
            )
        app = web.Application()
        app.add_routes([web.post("/webhooks/topic/{topic}/", self._receive_webhook)])
        runner = web.AppRunner(app)
        await runner.setup()
        self.webhook_site = web.TCPSite(runner, "0.0.0.0", webhook_port)
        await self.webhook_site.start()
        print("Listening to web_hooks on port", webhook_port)

    async def _receive_webhook(self, request: ClientRequest):
        topic = request.match_info["topic"]
        payload = await request.json()
        await self.handle_webhook(topic, payload)
        # TODO web hooks don't require a response???
        return web.Response(text="")

    async def handle_webhook(self, topic: str, payload):
        if topic != "webhook":  # would recurse
            handler = f"handle_{topic}"
            method = getattr(self, handler, None)
            # put a log message here
            log_msg('Passing payload to handler ' + handler + ' payload is: ' + json.dumps(payload))
            if method:
                await method(payload)
            else:
                log_msg(
                    f"Error: agent {self.ident} "
                    f"has no method {handler} "
                    f"to handle webhook on topic {topic}"
                )
        else:
            log_msg('in webhook, topic is: ' + topic + ' payload is: ' + json.dumps(payload))

    async def handle_connections(self, message):
        connection_id = message["connection_id"]
        push_resource(connection_id, "connection-msg", message)
        # put a log message here (all the handle_ )
        # TODO wait here to determine the response to the web hook?????
        pass

    async def handle_issue_credential(self, message):
        thread_id = message["thread_id"]
        push_resource(thread_id, "credential-msg", message)
        # put a log message here (all the handle_ )
        # TODO wait here to determine the response to the web hook?????
        pass

    async def handle_present_proof(self, message):
        thread_id = message["thread_id"]
        push_resource(thread_id, "presentation-msg", message)
        # put a log message here (all the handle_ )
        # TODO wait here to determine the response to the web hook?????
        pass

    async def swap_thread_id_for_exchange_id(self, thread_id, data_type, id_txt):
        await asyncio.sleep(2)
        msg = get_resource(thread_id, data_type)
        ex_id = msg[0][id_txt]
        return ex_id

    async def make_admin_request(
        self, method, path, data=None, text=False, params=None
    ) -> (int, str):
        params = {k: v for (k, v) in (params or {}).items() if v is not None}
        async with self.client_session.request(
            method, self.admin_url + path, json=data, params=params
        ) as resp:
            resp_status = resp.status
            resp_text = await resp.text()
            return (resp_status, resp_text)

    async def admin_GET(self, path, text=False, params=None) -> (int, str):
        try:
            return await self.make_admin_request("GET", path, None, text, params)
        except ClientError as e:
            self.log(f"Error during GET {path}: {str(e)}")
            raise

    async def admin_POST(
        self, path, data=None, text=False, params=None
    ) -> (int, str):
        try:
            return await self.make_admin_request("POST", path, data, text, params)
        except ClientError as e:
            self.log(f"Error during POST {path}: {str(e)}")
            raise

    async def make_agent_POST_request(
        self, op, rec_id=None, data=None, text=False, params=None
    ) -> (int, str):
        if op["topic"] == "connection":
            operation = op["operation"]
            if operation == "create-invitation":
                agent_operation = "/connections/" + operation

                (resp_status, resp_text) = await self.admin_POST(agent_operation)

                # extract invitation from the agent's response
                invitation_resp = json.loads(resp_text)
                resp_text = json.dumps(invitation_resp)

                if resp_status == 200: resp_text = self.agent_state_translation(op["topic"], operation, resp_text)
                return (resp_status, resp_text)

            elif operation == "receive-invitation":
                agent_operation = "/connections/" + operation

                (resp_status, resp_text) = await self.admin_POST(agent_operation, data=data)
                if resp_status == 200: resp_text = self.agent_state_translation(op["topic"], None, resp_text)
                return (resp_status, resp_text)

            elif (operation == "accept-invitation" 
                or operation == "accept-request"
                or operation == "remove"
                or operation == "start-introduction"
                or operation == "send-ping"
            ):
                connection_id = rec_id
                agent_operation = "/connections/" + connection_id + "/" + operation
                log_msg('POST Request: ', agent_operation, data)

                (resp_status, resp_text) = await self.admin_POST(agent_operation, data)

                log_msg(resp_status, resp_text)
                if resp_status == 200: resp_text = self.agent_state_translation(op["topic"], None, resp_text)
                return (resp_status, resp_text)

        elif op["topic"] == "schema":
            # POST operation is to create a new schema
            agent_operation = "/schemas"
            log_msg(agent_operation, data)

            (resp_status, resp_text) = await self.admin_POST(agent_operation, data)

            log_msg(resp_status, resp_text)
            return (resp_status, resp_text)

        elif op["topic"] == "credential-definition":
            # POST operation is to create a new cred def
            agent_operation = "/credential-definitions"
            log_msg(agent_operation, data)

            (resp_status, resp_text) = await self.admin_POST(agent_operation, data)

            log_msg(resp_status, resp_text)
            return (resp_status, resp_text)

        elif op["topic"] == "issue-credential":
            operation = op["operation"]
            if rec_id is None:
                agent_operation = "/issue-credential/" + operation
            else:
                if (operation == "send-offer" 
                    or operation == "send-request"
                    or operation == "issue"
                    or operation == "store"
                ):
                    # swap thread id for cred ex id from the webhook
                    cred_ex_id = await self.swap_thread_id_for_exchange_id(rec_id, "credential-msg","credential_exchange_id")
                    agent_operation = "/issue-credential/records/" + cred_ex_id + "/" + operation
                else:
                    agent_operation = "/issue-credential/" + operation
            
            log_msg(agent_operation, data)
            
            (resp_status, resp_text) = await self.admin_POST(agent_operation, data)

            log_msg(resp_status, resp_text)
            if resp_status == 200: resp_text = self.agent_state_translation(op["topic"], None, resp_text)
            return (resp_status, resp_text)

        elif op["topic"] == "proof":
            operation = op["operation"]
            if operation == "create-send-connectionless-request":
                operation = "create-request"
            if rec_id is None:
                agent_operation = "/present-proof/" + operation
            else:
                if (operation == "send-presentation" 
                    or operation == "send-request"
                    or operation == "verify-presentation"
                    or operation == "remove"
                ):
                    #pres_ex_id = rec_id
                    # swap thread id for pres ex id from the webhook
                    pres_ex_id = await self.swap_thread_id_for_exchange_id(rec_id, "presentation-msg", "presentation_exchange_id")
                    agent_operation = "/present-proof/records/" + pres_ex_id + "/" + operation
                else:
                    agent_operation = "/present-proof/" + operation
            
            log_msg(agent_operation, data)
            # Format the message data that came from the test, to what the Aca-py admin api expects.
            data = self.map_test_json_to_admin_api_json(op["topic"], operation, data)

            (resp_status, resp_text) = await self.admin_POST(agent_operation, data)

            log_msg(resp_status, resp_text)
            if resp_status == 200: resp_text = self.agent_state_translation(op["topic"], None, resp_text)
            return (resp_status, resp_text)

        return (501, '501: Not Implemented\n\n'.encode('utf8'))

    async def make_agent_GET_request(
        self, op, rec_id=None, text=False, params=None
    ) -> (int, str):
        if op["topic"] == "status":
            status = 200 if self.ACTIVE else 418
            status_msg = "Active" if self.ACTIVE else "Inactive"
            return (status, json.dumps({"status": status_msg}))

        elif op["topic"] == "connection":
            if rec_id:
                connection_id = rec_id
                agent_operation = "/connections/" + connection_id
            else:
                agent_operation = "/connections"
            
            log_msg('GET Request agent operation: ', agent_operation)

            (resp_status, resp_text) = await self.admin_GET(agent_operation)
            if resp_status != 200:
                return (resp_status, resp_text)

            log_msg('GET Request response details: ', resp_status, resp_text)

            resp_json = json.loads(resp_text)
            if rec_id:
                connection_info = {"connection_id": resp_json["connection_id"], "state": resp_json["state"], "connection": resp_json}
                resp_text = json.dumps(connection_info)
            else:
                resp_json = resp_json["results"]
                connection_infos = []
                for connection in resp_json:
                    connection_info = {"connection_id": connection["connection_id"], "state": connection["state"], "connection": connection}
                    connection_infos.append(connection_info)
                resp_text = json.dumps(connection_infos)
            # translate the state from that the agent gave to what the tests expect
            resp_text = self.agent_state_translation(op["topic"], None, resp_text)
            return (resp_status, resp_text)

        elif op["topic"] == "did":
            agent_operation = "/wallet/did/public"

            (resp_status, resp_text) = await self.admin_GET(agent_operation)
            if resp_status != 200:
                return (resp_status, resp_text)

            resp_json = json.loads(resp_text)
            did = resp_json["result"]

            resp_text = json.dumps(did)
            return (resp_status, resp_text)

        elif op["topic"] == "schema":
            schema_id = rec_id
            agent_operation = "/schemas/" + schema_id

            (resp_status, resp_text) = await self.admin_GET(agent_operation)
            if resp_status != 200:
                return (resp_status, resp_text)

            resp_json = json.loads(resp_text)
            schema = resp_json["schema"]

            resp_text = json.dumps(schema)
            return (resp_status, resp_text)

        elif op["topic"] == "credential-definition":
            cred_def_id = rec_id
            agent_operation = "/credential-definitions/" + cred_def_id

            (resp_status, resp_text) = await self.admin_GET(agent_operation)
            if resp_status != 200:
                return (resp_status, resp_text)

            resp_json = json.loads(resp_text)
            credential_definition = resp_json["credential_definition"]

            resp_text = json.dumps(credential_definition)
            return (resp_status, resp_text)

        elif op["topic"] == "issue-credential":
            # swap thread id for cred ex id from the webhook
            cred_ex_id = await self.swap_thread_id_for_exchange_id(rec_id, "credential-msg","credential_exchange_id")
            agent_operation = "/issue-credential/records/" + cred_ex_id

            (resp_status, resp_text) = await self.admin_GET(agent_operation)
            if resp_status == 200: resp_text = self.agent_state_translation(op["topic"], None, resp_text)
            return (resp_status, resp_text)

        elif op["topic"] == "credential":
            agent_operation = "/credential/" + rec_id

            (resp_status, resp_text) = await self.admin_GET(agent_operation)
            return (resp_status, resp_text)

        elif op["topic"] == "proof":
            # swap thread id for pres ex id from the webhook
            pres_ex_id = await self.swap_thread_id_for_exchange_id(rec_id, "presentation-msg", "presentation_exchange_id")
            agent_operation = "/present-proof/records/" + pres_ex_id

            (resp_status, resp_text) = await self.admin_GET(agent_operation)
            if resp_status == 200: resp_text = self.agent_state_translation(op["topic"], None, resp_text)
            return (resp_status, resp_text)

        return (501, '501: Not Implemented\n\n'.encode('utf8'))

    async def make_agent_GET_request_response(
        self, topic, rec_id=None, text=False, params=None
    ) -> (int, str):
        if topic == "connection" and rec_id:
            connection_msg = pop_resource(rec_id, "connection-msg")
            i = 0
            while connection_msg is None and i < MAX_TIMEOUT:
                sleep(1)
                connection_msg = pop_resource(rec_id, "connection-msg")
                i = i + 1

            resp_status = 200
            if connection_msg:
                resp_text = json.dumps(connection_msg)
            else:
                resp_text = "{}"

            return (resp_status, resp_text)

        elif topic == "issue-credential" and rec_id:
            credential_msg = pop_resource(rec_id, "credential-msg")
            i = 0
            while credential_msg is None and i < MAX_TIMEOUT:
                sleep(1)
                credential_msg = pop_resource(rec_id, "credential-msg")
                i = i + 1

            resp_status = 200
            if credential_msg:
                resp_text = json.dumps(credential_msg)
            else:
                resp_text = "{}"

            return (resp_status, resp_text)

        elif topic == "credential" and rec_id:
            credential_msg = pop_resource(rec_id, "credential-msg")
            i = 0
            while credential_msg is None and i < MAX_TIMEOUT:
                sleep(1)
                credential_msg = pop_resource(rec_id, "credential-msg")
                i = i + 1

            resp_status = 200
            if credential_msg:
                resp_text = json.dumps(credential_msg)
            else:
                resp_text = "{}"

            return (resp_status, resp_text)
        
        elif topic == "proof" and rec_id:
            presentation_msg = pop_resource(rec_id, "presentation-msg")
            i = 0
            while presentation_msg is None and i < MAX_TIMEOUT:
                sleep(1)
                presentation_msg = pop_resource(rec_id, "presentation-msg")
                i = i + 1

            resp_status = 200
            if presentation_msg:
                resp_text = json.dumps(presentation_msg)
                if resp_status == 200: resp_text = self.agent_state_translation(topic, None, resp_text)
            else:
                resp_text = "{}"
            
            return (resp_status, resp_text)

        return (501, '501: Not Implemented\n\n'.encode('utf8'))

    def _process(self, args, env, loop):
        proc = subprocess.Popen(
            args,
            env=env,
            encoding="utf-8",
        )
        loop.run_in_executor(
            None,
            output_reader,
            proc.stdout,
            functools.partial(self.handle_output, source="stdout"),
        )
        loop.run_in_executor(
            None,
            output_reader,
            proc.stderr,
            functools.partial(self.handle_output, source="stderr"),
        )
        return proc

    def get_process_args(self, bin_path: str = None):
        #TODO aca-py needs to be in the path so no need to give it a cmd_path
        cmd_path = "aca-py"
        if bin_path is None:
            bin_path = DEFAULT_BIN_PATH
        if bin_path:
            cmd_path = os.path.join(bin_path, cmd_path)
        print ('Location of ACA-Py: ' + cmd_path)
        return list(flatten((["python3", cmd_path, "start"], self.get_agent_args())))

    async def detect_process(self):
        text = None

        async def fetch_swagger(url: str, timeout: float):
            text = None
            start = default_timer()
            async with ClientSession(timeout=ClientTimeout(total=3.0)) as session:
                while default_timer() - start < timeout:
                    try:
                        async with session.get(url) as resp:
                            if resp.status == 200:
                                text = await resp.text()
                                break
                    except (ClientError, asyncio.TimeoutError):
                        pass
                    await asyncio.sleep(0.5)
            return text

        status_url = self.admin_url + "/status"
        status_text = await fetch_swagger(status_url, START_TIMEOUT)
        print("Agent running with admin url", self.admin_url)

        if not status_text:
            raise Exception(
                "Timed out waiting for agent process to start. "
                + f"Admin URL: {status_url}"
            )
        ok = False
        try:
            status = json.loads(status_text)
            ok = isinstance(status, dict) and "version" in status
        except json.JSONDecodeError:
            pass
        if not ok:
            raise Exception(
                f"Unexpected response from agent process. Admin URL: {status_url}"
            )

    async def start_process(
        self, python_path: str = None, bin_path: str = None, wait: bool = True
    ):
        my_env = os.environ.copy()
        python_path = DEFAULT_PYTHON_PATH if python_path is None else python_path
        if python_path:
            my_env["PYTHONPATH"] = python_path

        agent_args = self.get_process_args(bin_path)

        # start agent sub-process
        self.log(f"Starting agent sub-process ...")
        self.log(f"agent starting with params: ")
        self.log(agent_args)
        loop = asyncio.get_event_loop()
        self.proc = await loop.run_in_executor(
            None, self._process, agent_args, my_env, loop
        )
        if wait:
            await asyncio.sleep(1.0)
            await self.detect_process()

    def _terminate(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=0.5)
                self.log(f"Exited with return code {self.proc.returncode}")
            except subprocess.TimeoutExpired:
                msg = "Process did not terminate in time"
                self.log(msg)
                raise Exception(msg)

    async def terminate(self):
        loop = asyncio.get_event_loop()
        if self.proc:
            await loop.run_in_executor(None, self._terminate)
        await self.client_session.close()
        if self.webhook_site:
            await self.webhook_site.stop()

    def map_test_json_to_admin_api_json(self, topic, operation, data):
        # If the translation of the json get complicated in the future we might want to consider a switch to JsonMapper or equivalent.
        #json_mapper = JsonMapper()
        # map_specification = {
        #     'name': ['person_name']
        # }
        #JsonMapper(test_json).map(map_specification)

        if topic == "proof":

            if operation == "send-request" or operation == "create-request":
                
                if data.get("presentation_proposal", {}).get("request_presentations~attach", {}).get("data", {}).get("requested_values") == None:
                    requested_attributes = {}
                else:
                    requested_attributes = data["presentation_proposal"]["request_presentations~attach"]["data"]["requested_values"]

                if data.get("presentation_proposal", {}).get("request_presentations~attach", {}).get("data", {}).get("requested_predicates") == None:
                    requested_predicates = {}
                else:
                    requested_predicates = data["presentation_proposal"]["request_presentations~attach"]["data"]["requested_predicates"]

                if data.get("presentation_proposal", {}).get("request_presentations~attach", {}).get("data", {}).get("name") == None:
                    proof_request_name = "test proof"
                else:
                    proof_request_name = data["presentation_proposal"]["request_presentations~attach"]["data"]["name"]

                if data.get("presentation_proposal", {}).get("request_presentations~attach", {}).get("data", {}).get("version") == None:
                    proof_request_version = "1.0"
                else:
                    proof_request_version = data["presentation_proposal"]["request_presentations~attach"]["data"]["version"]
                
                if "connection_id" in data:
                    admin_data = {
                        "comment": data["presentation_proposal"]["comment"],
                        "trace": False,
                        "connection_id": data["connection_id"],
                        "proof_request": {
                            "name": proof_request_name,
                            "version": proof_request_version,
                            "requested_attributes": requested_attributes,
                            "requested_predicates": requested_predicates
                        }
                    }
                else:
                    admin_data = {
                        "comment": data["presentation_proposal"]["comment"],
                        "trace": False,
                        "proof_request": {
                            "name": proof_request_name,
                            "version": proof_request_version,
                            "requested_attributes": requested_attributes,
                            "requested_predicates": requested_predicates
                        }
                    }

            elif operation == "send-presentation":
                
                if data.get("requested_attributes") == None:
                    requested_attributes = {}
                else:
                    requested_attributes = data["requested_attributes"]

                if data.get("requested_predicates") == None:
                    requested_predicates = {}
                else:
                    requested_predicates = data["requested_predicates"]

                if data.get("self_attested_attributes") == None:
                    self_attested_attributes = {}
                else:
                    self_attested_attributes = data["self_attested_attributes"]

                admin_data = {
                    "comment": data["comment"],
                    "requested_attributes": requested_attributes,
                    "requested_predicates": requested_predicates,
                    "self_attested_attributes": self_attested_attributes
                }

            else:
                admin_data = data

            return (admin_data)

    def agent_state_translation(self, topic, operation, data):
            # This method is used to translate the agent states passes back in the responses of operations into the states the 
            # test harness expects. The test harness expects states to be as they are written in the Protocol's RFC.
            # the following is what the tests/rfc expect vs what aca-py communicates
            # Connection Protocol:
            # Tests/RFC         |   Aca-py
            # invited           |   invitation
            # requested         |   request
            # responded         |   response
            # complete          |   active
            #
            # Issue Credential Protocol:
            # Tests/RFC         |   Aca-py
            # proposal-sent     |   proposal_sent
            # proposal-received |   proposal_received
            # offer-sent        |   offer_sent
            # offer_received    |   offer_received
            # request-sent      |   request_sent
            # request-received  |   request_received
            # credential-issued |   issued
            # credential-received | credential_received
            # done              |   credential_acked
            #
            # Present Proof Protocol:
            # Tests/RFC         |   Aca-py

            resp_json = json.loads(data)
            # Check to see if state is in the json
            if "state" in resp_json:
                agent_state = resp_json["state"]
                if topic == "connection":
                    data = data.replace(agent_state, self.connectionStateTranslationDict[agent_state])
                elif topic == "issue-credential":
                    data = data.replace(agent_state, self.issueCredentialStateTranslationDict[agent_state])
                elif topic == "proof":
                    data = data.replace(agent_state, self.presentProofStateTranslationDict[agent_state])
            return (data)


async def main(start_port: int, show_timing: bool = False, interactive: bool = True):

    genesis = await default_genesis_txns()
    if not genesis:
        print("Error retrieving ledger genesis transactions")
        sys.exit(1)

    agent = None

    try:
        agent = AcaPyAgentBackchannel(
            "aca-py", start_port+1, start_port+2, genesis_data=genesis
        )

        # start backchannel (common across all types of agents)
        await agent.listen_backchannel(start_port)

        # start aca-py agent sub-process and listen for web hooks
        await agent.listen_webhooks(start_port+3)
        await agent.register_did()

        await agent.start_process()
        agent.activate()

        # now wait ...
        if interactive:
            async for option in prompt_loop(
                "(X) Exit? [X] "
            ):
                if option is None or option in "xX":
                    break
        else:
            print("Press Ctrl-C to exit ...")
            remaining_tasks = asyncio.Task.all_tasks()
            await asyncio.gather(*remaining_tasks)

    finally:
        terminated = True
        try:
            if agent:
                await agent.terminate()
        except Exception:
            LOGGER.exception("Error terminating agent:")
            terminated = False

    await asyncio.sleep(0.1)

    if not terminated:
        os._exit(1)

def str2bool(v):
    if isinstance(v, bool):
       return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Runs a Faber demo agent.")
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=8020,
        metavar=("<port>"),
        help="Choose the starting port number to listen on",
    )
    parser.add_argument(
        "-i",
        "--interactive",
        type=str2bool,
        default=True,
        metavar=("<interactive>"),
        help="Start agent interactively",
    )
    args = parser.parse_args()

    require_indy()

    try:
        asyncio.get_event_loop().run_until_complete(main(start_port=args.port, interactive=args.interactive))
    except KeyboardInterrupt:
        os._exit(1)
