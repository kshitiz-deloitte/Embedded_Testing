import json

import requests
import responses
from responses import matchers
from responses.matchers import multipart_matcher
from responses.registries import OrderedRegistry
import pytest

from Test.Utils.readCfg import get_from_config

base_url = get_from_config("base_url")


class TestCasesRebootReason:

    @responses.activate(registry=OrderedRegistry)
    def test_reboot_reason_(self):
        path = get_from_config("path_reboot_reason")
        responses.get(
            f"{base_url}{path}",
            json={"Reboot reason": "System failure"},
            status=200
        )
        responses.get(
            f"{base_url}{path}",
            body="Internal server error",
            status=500
        )
        responses.get(
            f"{base_url}{path}",
            body="Service unavailable",
            status=503
        )
        req = requests.get(f"{base_url}{path}")
        assert req.status_code == 200
        print(f"\n{req.json()['Reboot reason']}")

        req1 = requests.get(f"{base_url}{path}")
        assert req1.status_code == 500
        assert req1.text == "Internal server error"

        req2 = requests.get(f"{base_url}{path}")
        assert req2.status_code == 503
        assert req2.text == "Service unavailable"

    @responses.activate
    def test_process_running(self):
        process_name = "SQL_database"
        path = get_from_config("path_process_status")
        responses.get(
            f"{base_url}{path}{process_name}",
            json={"Process name": process_name, "Status": "Running"},
            status=200
        )
        responses.post(
            f"{base_url}{path}{process_name}",
            body="Method not allowed",
            status=405
        )
        req = requests.get(f"{base_url}{path}{process_name}")
        assert req.json()["Process name"] == process_name
        assert req.status_code == 200
        print(f"\nProcess name = {req.json()['Process name']}, status = {req.json()['Status']}")

        req1 = requests.post(f"{base_url}{path}{process_name}")
        assert req1.text == "Method not allowed"
        assert req1.status_code == 405

    @responses.activate
    def test_set_trigger_pulse_time(self):
        path = get_from_config("path_set_trigger_pulse_time")
        data = {"sec": "1234", "nsec": "1234"}
        responses.post(
            f"{base_url}{path}",
            match=[matchers.urlencoded_params_matcher(data)],
            json={"status": "successful"},
            status=201
        )
        responses.delete(
            f"{base_url}{path}",
            body="Bad request",
            status=400
        )
        req = requests.post(f"{base_url}{path}", data=data)
        assert req.headers == {"Content-type": "application/json"}
        assert req.json()['status'] == "successful"
        assert req.status_code == 201

        req1 = requests.delete(f"{base_url}{path}", data=data)
        assert req1.status_code == 400
        assert req1.text == "Bad request"

    @responses.activate
    def test_set_trigger_pulse_interval(self):
        data = {"sec": "1234", "nsec": "1234"}
        path = get_from_config("path_set_trigger_pulse_interval")
        responses.post(
            f"{base_url}{path}",
            match=[matchers.urlencoded_params_matcher(data)],
            json={"status": "successful"},
            status=201
        )
        req = requests.post(f"{base_url}{path}", data=data)
        assert req.json()['status'] == "successful"
        assert req.status_code == 201
        assert req.headers == {"Content-type": "application/json"}

    @responses.activate
    def test_enable_trigger_pulse(self):
        path = get_from_config("path_enable_trigger_pulse")
        data = {"enable": "1"}
        responses.post(
            f"{base_url}{path}",
            match=[matchers.urlencoded_params_matcher(data)],
            json={"Enabled": True},  # initially trigger pulse is disabled
            status=202
        )
        req = requests.post(f"{base_url}{path}", data=data)
        assert req.json()["Enabled"] is True
        assert req.status_code == 202
        assert req.headers == {"Content-type": "application/json"}

    @responses.activate()
    def test_trigger_pulse_status(self):
        path = get_from_config("path_get_trigger_pulse_status")
        responses.get(
            f"{base_url}{path}",
            json={"Status": "Enabled"},
            status=200
        )
        responses.post(
            f"{base_url}{path}",
            body="Method not allowed",
            status=405
        )
        req = requests.get(f"{base_url}{path}")
        print(f"\n{req.json()}")
        assert req.status_code == 200

        req1 = requests.post(f"{base_url}{path}")
        print(f"\n{req1.text}")
        assert req1.text == "Method not allowed"
        assert req1.status_code == 405

    @responses.activate
    def test_stress_ng(self):
        path = get_from_config("path_stressng")
        def request_callback(request):
            payload = json.loads(request.body)
            resp_body = {"cpu": payload['cpu'], "io": payload["io"], "vm": payload['vm'],
                         "vm-bytes": payload['vm-bytes'], "time": payload['time'], "temp-path": payload['temp-path'],
                         "backoff": payload['backoff'], "persist": payload['persist'], "enable": payload['enable']}
            headers = {"request-id": "728d329e-0e86-11e4-a748-0c84dc037c13"}
            return 201, headers, json.dumps(resp_body)

        responses.add_callback(
            responses.POST,
            f"{base_url}{path}",
            callback=request_callback
        )
        req = requests.post(
            f"{base_url}{path}",
            json.dumps({"cpu": "8", "io": "4", "vm": '2',
                        "vm-bytes": "56889", "time": "10 min", "temp-path": "temppath",
                        "backoff": "200", "persist": True, "enable": True}),
            headers={"content-type": "application/json"}
        )
        assert req.status_code == 201
        assert req.url == f"{base_url}{path}"

    @responses.activate
    def test_stress_ng_status(self):
        path = get_from_config("path_stressng_status")
        responses.get(
            f"{base_url}{path}",
            json={
                "api": "api/v1.0/{path}",
                "status": "success",
                "svc_status": {
                    "argument_string": "",
                    "is_running": False
                }
            },
            status=200
        )
        responses.post(
            f"{base_url}{path}",
            body="Bad request",
            status=400
        )
        req = requests.get(f"{base_url}{path}")
        assert req.headers == {"Content-Type": "application/json"}
        assert req.json()['api'] == "api/v1.0/{path}"
        assert req.status_code == 200

        req2 = requests.post(f"{base_url}{path}")
        assert req2.headers == {"Content-Type": "text/plain"}
        assert req2.status_code == 400
        assert req2.text == "Bad request"
        
