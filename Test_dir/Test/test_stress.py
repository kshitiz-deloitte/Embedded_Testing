import json
import time
import requests
import responses
from datetime import datetime
from responses import matchers

from Test.Utils.readCfg import get_from_config

base_url = get_from_config("base_url")


class TestStress:

    # Testing API to get software version
    @responses.activate
    def test_software_version(self):
        path = get_from_config("path_software_version")
        responses.add(responses.Response(method="GET",
                                         url=f"{base_url}{path}",
                                         json={
                                             "api": "/api/v1.0/swupdate/sw-versions",
                                             "status": "success",
                                             "versions":
                                                 {
                                                     "name": "Cruise 1.0",
                                                     "version": "1.0"
                                                 }
                                         },
                                         status=200
                                         ))

        responses.add(responses.Response(
            method="POST",
            url=f"{base_url}{path}",
            status=400
        ))
        responses.put(
            url=f"{base_url}{path}",
            status=400
        )

        req = requests.get(f"{base_url}{path}")
        req1 = requests.post(f"{base_url}{path}")
        req2 = requests.put(f"{base_url}{path}")

        dictionary = req.json()
        assert dictionary["api"] == "/api/v1.0/swupdate/sw-versions"
        assert dictionary["status"] == "success"
        assert dictionary["versions"]["name"] == "Cruise 1.0"
        assert dictionary["versions"]["version"] >= "1.0"
        assert req.status_code == 200

        assert req1.status_code == 400
        assert req2.status_code == 400
        print()
        if float(req.json()["versions"]['version']) < 1.0:
            print("Update required")

    # Testing API to get hardware version
    @responses.activate
    def test_hardware_version(self):
        path = get_from_config("path_hardware_version")
        responses.add(responses.Response(method="GET",
                                         url=f"{base_url}{path}",
                                         json={
                                             "api": "/api/v1.0/swupdate/hw-revision",
                                             "status": "success",
                                             "board": "Cruiseboardname",
                                             "revision": "1.1"
                                         },
                                         status=200
                                         ))
        responses.add(responses.patch(
            f"{base_url}{path}",
            body="Method not allowed",
            status=405
        ))

        # requests
        req = requests.get(f"{base_url}{path}")
        req1 = requests.patch(f"{base_url}{path}")

        # assertions
        assert req.json()['api'] == "/api/v1.0/swupdate/hw-revision"
        assert req.json()['status'] == "success"
        assert req.json()['board'] == "Cruiseboardname"
        assert req.json()['revision'] >= "1.1"
        assert req.status_code == 200

        assert req1.status_code == 405
        assert req1.text == "Method not allowed"

    # Testing API to get current system time
    @responses.activate
    def test_current_system_time(self):
        current_time = datetime.now().strftime("%H:%M")
        path = get_from_config("path_current_time")
        resp = responses.Response(
            method="GET",
            url=f"{base_url}{path}",
            json={"System time": current_time},
            status=200
        )
        responses.add(resp)
        responses.put(
            f"{base_url}{path}",
            body="Bad request",
            status=400
        )
        req = requests.get(f"{base_url}{path}")
        req1 = requests.put(f"{base_url}{path}")
        assert req.json()['System time'] == datetime.now().strftime("%H:%M")
        assert req.status_code == 200
        assert req1.status_code == 400
        assert req1.text == "Bad request"

    # Testing API to get boot status
    @responses.activate
    def test_boot_status(self):
        path = get_from_config("path_boot_status")
        responses.add(responses.Response(
            method="GET",
            url=f"{base_url}{path}",
            json={
                "api": "/api/v1.0/swupdate/boot-status",
                "boot-status": "success",
                "status": "Pass"
            },
            status=200
        ))
        responses.post(
            f"{base_url}{path}",
            body="Method Not Allowed",
            status=405
        )
        req = requests.get(f"{base_url}{path}")
        req1 = requests.post(f"{base_url}{path}")
        if req.json()['status'] == "Fail":
            print("Reset Device")

        assert req.json()['api'] == "/api/v1.0/swupdate/boot-status"
        assert req.json()['boot-status'] == "success"
        assert req.json()['status'] == "Pass"
        assert req.status_code == 200
        assert req1.text == "Method Not Allowed"
        assert req1.status_code == 405

    # Testing API to get humidity and temperature
    @responses.activate
    def test_humidity_and_temperature(self):
        intial_time = time.time()
        path = get_from_config("path_humid_temp")
        responses.add(responses.Response(
            method="GET",
            url=f"{base_url}{path}",
            json=[{
                "device_name": "device_relative_humidity",
                "readings": [7.7],
                "unit": "Relative Humidity (Percentage)"
            },
                {
                    "device_name": "device_temperature",
                    "readings": [55.799],
                    "unit": "Celsius"
                }],
            status=200
        ))
        responses.post(
            f"{base_url}{path}",
            body="Method Not Allowed",
            status=405
        )
        req = requests.get(f"{base_url}{path}")
        req1 = requests.post(f"{base_url}{path}")
        total_time = time.time() - intial_time
        assert req.status_code == 200
        assert req.json()[0]['device_name'] == "device_relative_humidity"
        assert req.json()[1]['device_name'] == "device_temperature"
        assert req.json()[1]['unit'] == "Celsius"
        assert req.json()[0]['unit'] == "Relative Humidity (Percentage)"
        assert req1.text == "Method Not Allowed"
        assert req1.status_code == 405
        assert total_time < 100
        assert 20 < req.json()[1]['Readings'] < 100

    # Testing API to set imx register
    @responses.activate
    def test_set_imx_register(self):
        register, register_value = "0x01", "100"
        path = get_from_config("path_set_imx_register")

        def request_callback(request):
            payload = json.loads(request.body)
            resp_body = [{
                "Status": "Success",
                "register_details": {
                    "register": payload["register"],
                    "register_value": payload["register_value"]
                }
            }]
            headers = {"request-id": "728d329e-0e86-11e4-a748-0c84dc037c13"}
            return 201, headers, json.dumps(resp_body)

        responses.add_callback(
            responses.POST,
            url=f"{base_url}{path}",
            callback=request_callback,
            content_type="application/json",
        )
        responses.get(
            f"{base_url}{path}",
            body="Bad request",
            status=400
        )

        req = requests.post(
            f"{base_url}{path}",
            json.dumps(
                {"register": [register],
                 "register_value": [register_value]}
            ),
            headers={"content-type": "application/json"}
        )
        resp = req.json()

        req2 = requests.get(f"{base_url}{path}")

        assert resp[0]['Status'] == "Success"
        assert resp[0]['register_details'] == {
            "register": [register],
            "register_value": [register_value]
        }
        assert req.status_code == 201

        assert req2.text == "Bad request"
        assert req2.status_code == 400

    # Testing API to get imx register
    @responses.activate
    def test_read_imx_value(self):
        param = "0x76"
        path = get_from_config("path_get_imx_register")
        responses.get(
            f"{base_url}{path}{param}",
            json={"Register": f"{param}", "Status": "Success"},
            status=200
        )
        responses.post(
            f"{base_url}{path}{param}",
            body="Method not allowed",
            status=405
        )
        req = requests.get(f"{base_url}{path}{param}")
        req1 = requests.post(f"{base_url}{path}{param}")
        assert req.json()['Register'] == param
        assert req.json()['Status'] == "Success"
        assert 20 < int(req.json()['Register'], 16) < 100
        assert req1.text == "Method not allowed"

        print(int(param, 16))

    # Testing API that manage stressapptest
    @responses.activate
    def test_stress_app(self):
        path = get_from_config("path_stress_app")

        def request_callback(request):
            payload = json.loads(request.body)
            resp_body = {"memory": payload['memory'], "copy_threads": payload['copy_threads'],
                         "cpu_threads": payload['cpu_threads'], "time": payload['time'],
                         "stressful_memory": payload['stressful_memory'], "tempfile": payload['tempfile'],
                         "persist": payload['persist'], "enable": payload['enable']}
            headers = {"request-id": "728d329e-0e86-11e4-a748-0c84dc037c13"}
            return 201, headers, json.dumps(resp_body)

        responses.add_callback(
            responses.POST,
            url=f"{base_url}{path}",
            callback=request_callback,
            content_type="application/json",
        )
        req = requests.post(
            f"{base_url}{path}",
            json.dumps(
                {"memory": 512, "copy_threads": 8,
                 "cpu_threads": 8, "time": 10,
                 "stressful_memory": False, "tempfile": ["/temp/file1", "/temp/file2"],
                 "persist": False, "enable": True}
            ),
            headers={"content-type": "application/json"}
        )
        resp = req.json()
        assert resp["memory"] == 512
        assert resp["cpu_threads"] == 8
        assert resp["copy_threads"] == 8
        assert resp["stressful_memory"] is False
        assert "/temp/file1" in resp["tempfile"] and "/temp/file2" in resp["tempfile"]
