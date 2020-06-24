#!/usr/bin/env python
# coding=utf-8

import boto3
import json
from configparser import ConfigParser
from os import environ
import random
import calendar
import time
from datetime import datetime
import psycopg2
from psycopg2.extras import LogicalReplicationConnection
import logging
import uuid


#globals
MODULE = "RDS-REPL"
PROFILE = "default"
REGION = "eu-west-2"
FILENAME = "local_cfg.ini"
IN_AWS = False


# logging config
logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

def get_config(filename='local_cfg.ini', section='changedata'):
    parser = ConfigParser()
    parser.read(filename)
    config = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            config[param[0]] = param[1]
    else:
        raise Exception(f'Section {section} not found in the {filename} file')
    return config

logging.info('using local config file')
MAIN_CONFIG = get_config(FILENAME,'changedata')
DB_CONFIG = get_config(FILENAME,'postgresql')

def createClient(region,service):
    if environ.get('CODEBUILD_BUILD_ID') is not None:
        logging.info('running in CodeBuild')
        return boto3.client(service, region_name=region)
    else:
        if IN_AWS:
            logging.info('running in AWS')
            return boto3.client(service, region_name=region)
        elif environ.get('ECS_RUN') is not None:
            logging.info('running in ECS')
            return boto3.client(service, region_name=region)
        else:
            logging.info(f'using AWS profile {PROFILE} for service:{service}')
            session = boto3.Session(profile_name=PROFILE)
            return session.client(service, region_name=region)

KINESIS_CLIENT = createClient(MAIN_CONFIG['region'],'kinesis')

def connect_to_db(dbconfig):
    try:
        conn = psycopg2.connect(**dbconfig,connection_factory=LogicalReplicationConnection)
    except (Exception, psycopg2.DatabaseError) as e:
        logging.error(f"connection error to {dbconfig['host']}:{dbconfig['database']} error {str(e)}")
        return
    else:
        logging.info(f"connected to {dbconfig['host']}:{dbconfig['database']}")
        return conn

def consume(msg):
    msg_list = msg.payload.split(" ")
    nw_msg = {"id": str(uuid.uuid1()),"time":str(datetime.utcnow()),"data":msg_list}
    try:
        result =KINESIS_CLIENT.put_record(StreamName=MAIN_CONFIG['stream_name'], Data=json.dumps(nw_msg), PartitionKey="default")
    except Exception as e:
        logging.error(f"failed to send msg error:{str(e)}")
    else:
        logging.info(json.dumps(nw_msg),result)


def main():
    logging.info(f"running {MODULE}")
    CONN = connect_to_db(DB_CONFIG)
    cur = CONN.cursor()
    cur.drop_replication_slot('cdc_test_slot')
    cur.create_replication_slot('cdc_test_slot',  output_plugin ='test_decoding')
    cur.start_replication(slot_name = 'cdc_test_slot', decode= True)
    cur.consume_stream(consume)


if __name__ == "__main__":
    main()

