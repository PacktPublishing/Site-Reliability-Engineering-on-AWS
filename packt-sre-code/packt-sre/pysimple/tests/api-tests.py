#!/usr/bin/env python
# coding=utf-8
import pytest
import requests
import logging

# logging config
logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

HOST="http://tf-ecs-simplepy-alb-140830557.eu-west-2.elb.amazonaws.com"
VER="v0.1"
URI = f"{HOST}/api/{VER}"

def get_data(url,method):
    try:
        if method == "get":
            response = requests.get(url)
        elif method == "post":
            response = requests.post(url)
        elif method == "patch":
            response = requests.patch(url)
        else:
            response = None
            logging.error(f"no supported method:{method}")
    except Exception as e:
        logging.error(f"error for {url} error:{str(e)}")
        response = None
    return response

def test_get_cars_data_returns_a_200_response_code_and_json_payload(get_cars_data):
    assert get_cars_data.status_code == 200, "response code was not 200"
    assert get_cars_data.headers['Content-Type'] == "application/json", "response Content-Type was not json"
    assert get_cars_data.json is not None, "response data is JSON"

@pytest.fixture
def get_cars_data():
    url = f"{URI}/cars"
    method = "get"
    return get_data(url,method)



