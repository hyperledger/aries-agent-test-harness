import asyncio
import functools
import json
import logging
import os
import traceback
import random
import subprocess
import sys
import prompt_toolkit
from prompt_toolkit.application import run_in_terminal
from prompt_toolkit.eventloop.defaults import use_asyncio_event_loop
from prompt_toolkit.patch_stdout import patch_stdout
from timeit import default_timer

import pygments
from pygments.filter import Filter
from pygments.lexer import Lexer
from pygments.lexers.data import JsonLdLexer
from prompt_toolkit.formatted_text import FormattedText, PygmentsTokens

from aiohttp import (
    web,
    ClientSession,
    ClientRequest,
    ClientResponse,
    ClientError,
    ClientTimeout,
)

from python.utils import require_indy, flatten, log_json, log_msg, log_timer, output_reader, prompt_loop, read_operations

import ptvsd
ptvsd.enable_attach()

LOGGER = logging.getLogger(__name__)

DEFAULT_POSTGRES = bool(os.getenv("POSTGRES"))
DEFAULT_INTERNAL_HOST = "127.0.0.1"
DEFAULT_EXTERNAL_HOST = "localhost"

START_TIMEOUT = float(os.getenv("START_TIMEOUT", 30.0))

RUN_MODE = os.getenv("RUNMODE")

GENESIS_URL = os.getenv("GENESIS_URL")
LEDGER_URL = os.getenv("LEDGER_URL")

if RUN_MODE == "docker":
    DEFAULT_INTERNAL_HOST = os.getenv("DOCKERHOST") or "host.docker.internal"
    DEFAULT_EXTERNAL_HOST = DEFAULT_INTERNAL_HOST
elif RUN_MODE == "pwd":
    DEFAULT_EXTERNAL_HOST = os.getenv("DOCKERHOST") or "host.docker.internal"


def get_ledger_url(ledger_url: str = None):
    if not ledger_url:
        ledger_url = LEDGER_URL
    if not ledger_url:
        ledger_url = f"http://{DEFAULT_EXTERNAL_HOST}:9000"

    return ledger_url


async def default_genesis_txns():
    genesis = None
    try:
        if GENESIS_URL:
            async with ClientSession() as session:
                print("From GENESIS_URL:", GENESIS_URL)
                async with session.get(GENESIS_URL) as resp:
                    genesis = await resp.text()
        elif RUN_MODE == "docker":
            async with ClientSession() as session:
                ledger_url = get_ledger_url()
                print("From ledger_url:", f"{ledger_url}/genesis")
                async with session.get(
                    f"{ledger_url}/genesis"
                ) as resp:
                    genesis = await resp.text()
        else:
            print("With local file:", "../local-genesis.txt")
            with open("../local-genesis.txt", "r") as genesis_file:
                genesis = genesis_file.read()
    except Exception:
        LOGGER.exception("Error loading genesis transactions:")
    return genesis


class AgentBackchannel:
    """
    Base class for building Aries agent backchannel adapters for integration into the interoperability test suite.

    Extend this base class and implement hooks to communicate with a specific agent.
    """

    def __init__(
        self, 
        ident: str,
        http_port: int,
        admin_port: int,
        genesis_data: str = None,
        params: dict = {}
    ):
        self.ACTIVE = False

        self.ident = ident
        self.http_port = http_port
        self.admin_port = admin_port
        self.genesis_data = genesis_data
        self.params = params
        rand_name = str(random.randint(100_000, 999_999))
        self.seed = ("my_seed_000000000000000000000000" + rand_name)[-32:]

        self.internal_host = DEFAULT_INTERNAL_HOST
        self.external_host = DEFAULT_EXTERNAL_HOST
        self.label = ident

        # may be set via ngrok
        agent_endpoint = os.getenv("AGENT_PUBLIC_ENDPOINT")
        if agent_endpoint:
            self.endpoint = agent_endpoint
        elif RUN_MODE == "pwd":
            self.endpoint = f"http://{self.external_host}".replace(
                "{PORT}", str(http_port)
            )
        else:
            self.endpoint = f"http://{self.external_host}:{http_port}"
        self.admin_url = f"http://{self.internal_host}:{admin_port}"

        self.storage_type = "indy"
        self.wallet_type = "indy"
        self.wallet_name = self.ident.lower().replace(" ", "") + rand_name
        self.wallet_key = self.ident + rand_name
        self.did = None
        self.postgres = False

        self.client_session: ClientSession = ClientSession()

    def activate(self, active: bool = True):
        self.ACTIVE = active

    async def listen_backchannel(self, backchannel_port):
        """ 
        Setup the routes to allow the test harness to send commands to and get replies
        from the Agent under test.

        Expected topics include:

            schema                 GET to return a list and POST to create/update
            credential-definition  GET to return a list and POST to create/update
            connection             GET to return a list or single; POST to create/update*
            issue-credential       GET to return a list or single; POST to create/update*
            credential             GET to return a list of single from wallet; POST to remove*
            proof                  GET to return a list or single; POST to create/update*

        GET with no parameters returns all
        GET with an "id" parameter will return a single record
        POST will submit a JSON payload
        POST* will contain an "operation" element within the payload to define the operation
        POST operations on existing records must contain an "id" element
        POST operations will contain a "data" element which is the payload to pass through to the agent

        E.g.:  POST to /agent/command/issue_credential { "operation":"send-proposal", "data":"{...}"}
        E.g.:  POST to /agent/command/issue_credential { "operation":"issue", "id":"<cred exch id>", "data":"{...}"}

        Operations for each topic are in the backchannel_operations.csv file, generated from
        the Google sheet at https://bit.ly/AriesTestHarnessScenarios
        """
        #operations_file = "../backchannel_operations.txt"
        #self.operations = read_operations(file_name=operations_file, parser="pipe")
        operations_file = "./backchannel_operations.csv"
        self.operations = read_operations(file_name=operations_file)

        app = web.Application()
        app.add_routes([web.post("/agent/command/{topic}/", self._post_command_backchannel)])
        app.add_routes([web.post("/agent/command/{topic}", self._post_command_backchannel)])
        app.add_routes([web.post("/agent/command/{topic}/{operation}/", self._post_command_backchannel)])
        app.add_routes([web.post("/agent/command/{topic}/{operation}", self._post_command_backchannel)])
        app.add_routes([web.get("/agent/command/{topic}/", self._get_command_backchannel)])
        app.add_routes([web.get("/agent/command/{topic}", self._get_command_backchannel)])
        app.add_routes([web.get("/agent/command/{topic}/{id}/", self._get_command_backchannel)])
        app.add_routes([web.get("/agent/command/{topic}/{id}", self._get_command_backchannel)])
        app.add_routes([web.get("/agent/command/{topic}/{operation}/{id}/", self._get_command_backchannel)])
        app.add_routes([web.get("/agent/command/{topic}/{operation}/{id}", self._get_command_backchannel)])
        app.add_routes([web.delete("/agent/command/{topic}/{id}/", self._delete_command_backchannel)])
        app.add_routes([web.delete("/agent/command/{topic}/{id}", self._delete_command_backchannel)])
        app.add_routes([web.get("/agent/response/{topic}/", self._get_response_backchannel)])
        app.add_routes([web.get("/agent/response/{topic}", self._get_response_backchannel)])
        app.add_routes([web.get("/agent/response/{topic}/{id}/", self._get_response_backchannel)])
        app.add_routes([web.get("/agent/response/{topic}/{id}", self._get_response_backchannel)])
        runner = web.AppRunner(app)
        await runner.setup()
        self.backchannel_site = web.TCPSite(runner, "0.0.0.0", backchannel_port)
        await self.backchannel_site.start()
        print("Listening to backchannel on port", backchannel_port)

    def match_operation(self, topic, method, payload=None, operation=None, rec_id=None):
        """
        Determine which agent operation we are trying to invoke
        """
        data = None
        if payload:
            if "id" in payload:
                rec_id = payload["id"]
            if "cred_ex_id" in payload:
                rec_id = payload["cred_ex_id"]
            if "data" in payload:
                data = payload["data"]
        for op in self.operations:
            if operation is not None:
                if (op["topic"] == topic and op["method"] == method and
                    ((rec_id and op["id"] == "Y") or (rec_id is None)) and
                    ((operation and op["operation"] == operation)) and
                    ((data and op["data"] == "Y") or (data is None))
                ):
                    print("Matched operation:", op)
                    return op
            else:
                if (op["topic"] == topic and op["method"] == method and
                    ((rec_id and op["id"] == "Y") or (rec_id is None)) and
                    ((method == "GET") or (operation and op["operation"] == operation) or (operation is None)) and
                    ((data and op["data"] == "Y") or (data is None))
                ):
                    print("Matched operation:", op)
                    return op

        return None

    def not_found_response(self, request):
        resp_text = "404 not found: " + str(request)
        return web.Response(body=resp_text.encode('utf8'), status=404)

    def not_implemented_response(self, operation):
        resp_text = "501 not implemented: " + str(operation)
        return web.Response(body=resp_text.encode('utf8'), status=501)

    async def _post_command_backchannel(self, request: ClientRequest):
        """
        Post a POST command to the agent.
        """
        topic = request.match_info["topic"]
        topic_operation = request.match_info["operation"] if "operation" in request.match_info else None
        payload = await request.json()

        try:
            operation = self.match_operation(topic, "POST", payload=payload, operation=topic_operation)
            if operation:
                try:
                    if "data" in payload:
                        data = payload["data"]
                    else:
                        data = None
                        
                    if "id" in payload:
                        rec_id = payload["id"]
                    elif "cred_ex_id" in payload:
                        rec_id = payload["cred_ex_id"]
                    else:
                        rec_id = None

                    (resp_status, resp_text) = await self.make_agent_POST_request(operation, rec_id=rec_id, data=data)

                    if resp_status == 200:
                        return web.Response(text=resp_text, status=resp_status)
                    elif resp_status == 404:
                        return self.not_found_response(json.dumps(operation))
                    elif resp_status == 501:
                        return self.not_implemented_response(json.dumps(operation))
                    else:
                        return web.Response(body=resp_text, status=resp_status)
                except NotImplementedError as ni_e:
                    return self.not_implemented_response(json.dumps(operation))

            return self.not_found_response(topic + " " + topic_operation)

        except Exception as e:
            print("Exception:", e)
            traceback.print_exc()
            return web.Response(body=str(e), status=500)

    async def _get_command_backchannel(self, request: ClientRequest):
        """
        Post a GET command to the agent.
        """
        topic = request.match_info["topic"]
        topic_operation = request.match_info["operation"] if "operation" in request.match_info else None


        if "id" in request.match_info:
            rec_id = request.match_info["id"]
        else:
            rec_id = None
        
        try:
            operation = self.match_operation(topic, "GET", operation=topic_operation, rec_id=rec_id)
            if operation:
                try:
                    (resp_status, resp_text) = await self.make_agent_GET_request(operation, rec_id=rec_id)

                    if resp_status == 200:
                        return web.Response(text=resp_text, status=resp_status)
                    elif resp_status == 404:
                        return self.not_found_response(json.dumps(operation))
                    elif resp_status == 501:
                        return self.not_implemented_response(json.dumps(operation))
                    else:
                        return web.Response(body=resp_text, status=resp_status)
                except NotImplementedError as ni_e:
                    return self.not_implemented_response(json.dumps(operation))

            return self.not_found_response(topic)

        except Exception as e:
            print("Exception:", e)
            traceback.print_exc()
            return web.Response(body=str(e), status=500)

    async def _delete_command_backchannel(self, request: ClientRequest):
            """
            Post a DELETE command to the agent.
            """
            topic = request.match_info["topic"]

            if "id" in request.match_info:
                rec_id = request.match_info["id"]
            else:
                rec_id = None

            try:
                operation = self.match_operation(topic, "DELETE", rec_id=rec_id)
                if operation:
                    try:
                        (resp_status, resp_text) = await self.make_agent_DELETE_request(operation, rec_id=rec_id)

                        if resp_status == 200:
                            return web.Response(text=resp_text, status=resp_status)
                        elif resp_status == 404:
                            return self.not_found_response(json.dumps(operation))
                        elif resp_status == 501:
                            return self.not_implemented_response(json.dumps(operation))
                        else:
                            return web.Response(body=resp_text, status=resp_status)
                    except NotImplementedError as ni_e:
                        return self.not_implemented_response(json.dumps(operation))

                return self.not_found_response(topic)

            except Exception as e:
                print("Exception:", e)
                traceback.print_exc()
                return web.Response(body=str(e), status=500)

    async def _get_response_backchannel(self, request: ClientRequest):
        """
        Get a response from the (remote) agent.
        """
        topic = request.match_info["topic"]
        if "id" in request.match_info:
            rec_id = request.match_info["id"]
        else:
            rec_id = None

        try:
            (resp_status, resp_text) = await self.make_agent_GET_request_response(topic, rec_id=rec_id)

            if resp_status == 200:
                return web.Response(text=resp_text, status=resp_status)
            elif resp_status == 404:
                return self.not_found_response(topic)
            elif resp_status == 501:
                return self.not_implemented_response(topic)
            else:
                return web.Response(body=resp_text, status=resp_status)

        except NotImplementedError as ni_e:
            return self.not_implemented_response(topic)
        except Exception as e:
            print("Exception:", e)
            traceback.print_exc()
            return web.Response(body=str(e), status=500)

    async def make_agent_POST_request(
        self, op, rec_id=None, data=None, text=False, params=None
    ) -> (int, str):
        """
        Override with agent-specific behaviour
        """
        raise NotImplementedError

    async def make_agent_GET_request(
        self, op, rec_id=None, text=False, params=None
    ) -> (int, str):
        """
        Override with agent-specific behaviour
        """
        raise NotImplementedError

    async def make_agent_GET_request_response(
        self, topic, rec_id=None, text=False, params=None
    ) -> (int, str):
        """
        Override with agent-specific behaviour
        """
        raise NotImplementedError

    def log(self, msg):
        print(msg)

    def handle_output(self, *output, source: str = None, **kwargs):
        end = "" if source else "\n"
        if source == "stderr":
            color = "fg:ansired"
        elif not source:
            color = self.color or "fg:ansiblue"
        else:
            color = None
        log_msg(*output, color=color, prefix=self.prefix_str, end=end, **kwargs)

    async def register_did(self, ledger_url: str = None, alias: str = None):
        ledger_url = get_ledger_url(ledger_url)
        data = {"alias": alias or self.ident, "seed": self.seed, "role": "TRUST_ANCHOR"}
        async with self.client_session.post(
            ledger_url + "/register", json=data
        ) as resp:
            if resp.status != 200:
                raise Exception(f"Error registering DID, response code {resp.status}")
            nym_info = await resp.json()
            self.did = nym_info["did"]
        self.log(f"Got DID: {self.did}")

