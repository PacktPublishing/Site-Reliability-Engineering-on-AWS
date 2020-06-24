#!/usr/bin/env python
# coding=utf-8
import pytest
import pytest_dependency
import requests
import logging
import json
import random
import string


# logging config
logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

HOST="http://tf-ecs-simplepy-alb-140830557.eu-west-2.elb.amazonaws.com"
CARS_MS = "http://127.0.0.1:8001"
VER="v0.1"
URI = f"{CARS_MS}/api/{VER}"
HEADERS = {'Content-Type': 'application/json'}


def randomString(stringLength=8):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))

CAR_REG = f"car-{randomString(4)}"
logging.info(f"testing with {CAR_REG}")

def get_data(url,method,headers,in_data):
    try:
        if method == "get":
            response = requests.get(url,headers=headers)
        elif method == "post":
            response = requests.post(url,headers=headers,data=json.dumps(in_data))
        elif method == "patch":
            response = requests.patch(url,headers=headers,data=json.dumps(in_data))
        elif method == "put":
            response = requests.put(url,headers=headers,data=json.dumps(in_data))
        else:
            response = None
            logging.error(f"no supported method:{method}")
    except Exception as e:
        logging.error(f"error for {url} error:{str(e)}")
        response = None
    else:
        logging.info(f"response code{response.status_code} json:{str(response.json)}")
    return response

@pytest.mark.dependency()
def test_post_car_data_returns_a_200_response_code_and_json_payload():
    url = f"{URI}/car"
    method = "post"
    data = {"registration": CAR_REG, "make": "ford", "colour": "pink", "capacity": "4"}
    response = get_data(url, method,HEADERS,data)
    assert response.status_code == 200, "response code was not 200"
    assert response.headers['Content-Type'] == "application/json", "response Content-Type was not json"
    assert response.json is not None, "response data is JSON"

@pytest.mark.dependency(depends=['test_post_car_data_returns_a_200_response_code_and_json_payload'])
def test_get_cars_data_returns_a_200_response_code_and_json_payload():
    url = f"{URI}/cars"
    method = "get"
    response = get_data(url, method, HEADERS,{})
    jdata = response.json()
    assert response.status_code == 200, "response code was not 200"
    assert response.headers['Content-Type'] == "application/json", "response Content-Type was not json"
    assert jdata is not None, "response data is JSON"
    assert CAR_REG in jdata['result'], "test registration is not in list"

@pytest.mark.dependency(depends=['test_post_car_data_returns_a_200_response_code_and_json_payload'])
def test_get_car_data_returns_a_200_response_code_and_json_payload():
    url = f"{URI}/car/{CAR_REG}"
    method = "get"
    response = get_data(url, method,HEADERS,{})
    assert response.status_code == 200, "response code was not 200"
    assert response.headers['Content-Type'] == "application/json", "response Content-Type was not json"
    assert response.json is not None, "response data is JSON"

@pytest.mark.dependency()
@pytest.mark.dependency(depends=['test_post_car_data_returns_a_200_response_code_and_json_payload'])
def test_put_car_data_returns_a_200_response_code_and_json_payload():
    url = f"{URI}/car/{CAR_REG}"
    method = "put"
    data = {"make":"ford","colour":"aqua-maroon","capacity":"4"}
    response = get_data(url, method,HEADERS,data)
    assert response.status_code == 200, "response code was not 200"
    assert response.headers['Content-Type'] == "application/json", "response Content-Type was not json"
    assert response.json is not None, "response data is JSON"

@pytest.mark.dependency(depends=['test_put_car_data_returns_a_200_response_code_and_json_payload'])
def test_get_car_data_returns_a_200_response_code_and_json_payload_and_has_updated_colour():
    url = f"{URI}/car/{CAR_REG}"
    method = "get"
    response = get_data(url, method,HEADERS,{})
    jdata = response.json()
    assert response.status_code == 200, "response code was not 200"
    assert response.headers['Content-Type'] == "application/json", "response Content-Type was not json"
    assert response.json is not None, "response data is JSON"
    assert jdata[CAR_REG]['colour'] == 'aqua-maroon', "colour data has not been updated"









