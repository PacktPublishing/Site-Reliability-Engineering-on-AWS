#!/usr/bin/env python
# coding=utf-8

import logging
import boto3
import json
from os import environ
import requests
URL = "http://169.254.169.254/latest/meta-data/public-ipv4"
IN_AWS = False

try:
 response = requests.get(URL,timeout=1)
except Exception as e:
    logging.error(f"cannot connect to url:{URL} assuming not in AWS")
else:
    print(response.txt)
    logging.info(f"got {response.text} from meta data server")
    IN_AWS = True


#GlOBALS
MODULE = "AWS-helper"
PROFILE = "default"
REGION = "eu-west-2"

# logging config
logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

def createClient(region,service):
    if environ.get('CODEBUILD_BUILD_ID') is not None:
        return boto3.client(service, region_name=region)
    elif IN_AWS:
        return boto3.client(service, region_name=region)
    elif environ.get('ECS_RUN') is not None:
        return boto3.client(service, region_name=region)
    else:
        logging.info(f'using AWS profile {PROFILE} for service:{service}')
        session = boto3.Session(profile_name=PROFILE)
        return session.client(service, region_name=region)


def put_cloudwatch_metric(client,mname,a_name,c_name,m_value,uri,namespace):
    dimensions = [{'Name':'service','Value':a_name},{'Name':'component','Value':c_name},{'Name':'uri','Value':uri}]
    entry = {'MetricName':mname,'Dimensions':dimensions,'Unit':'None','Value':m_value}
    try:
        response = client.put_metric_data(MetricData=[entry],Namespace=namespace)
    except Exception as e:
        logging.error(f"put metric data error:{str(e)}")
        return
    else:
        logging.info(f"response:{response}")
        return response

def describe_rds_instance(client,instance_name):
    try:
        response = client.describe_db_instances(DBInstanceIdentifier=instance_name)
    except Exception as e:
        logging.error(f"error:{str(e)}")
        return
    else:
        logging.info(f"response:{response}")
        return response['DBInstances'][0]['DBInstanceArn']





