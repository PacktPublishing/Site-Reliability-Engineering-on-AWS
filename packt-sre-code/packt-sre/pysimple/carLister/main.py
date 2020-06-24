#!/usr/bin/env python
# coding=utf-8

import logging
import dbHelper as db
import awsHelper as aws
from configparser import ConfigParser
import json
from flask import request, Response, redirect,abort,make_response,jsonify
from flask import Flask
from eventlet import wsgi, monkey_patch, listen
import os
import sys


#GlOBALS
MODULE = "car-lister"
CONFIG_FILE = "local_cfg.ini"
SCHEMA = "schema.sql"
PORT = "8080"
DB_HEALTH = 0
REGION = "eu-west-2"

try:
    DB_HOST = os.environ['HOST']
    DB_NAME = os.environ['DB']
    DB_USER = os.environ['DB_USER']
    DB_PASS = os.environ['DB_PASS']
except KeyError as e:
    logging.error(f'Environment variable {e.args[0]} not set')
    DB_CONFIG = None
else:
    DB_CONFIG = {"host":DB_HOST,"database":DB_NAME,"user":DB_USER,"password":DB_PASS}
    logging.info('using environment variables')


# logging config
logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

#initialise flask
app = Flask(__name__)
app.secret_key = os.urandom(24)

def get_config(filename='local_cfg.ini', section='postgresql'):
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

#create DB connection
if DB_CONFIG ==  None:
    logging.info('using local config file')
    DB_CONFIG = get_config()
logging.info(f"connecting to database:{DB_CONFIG['database']} host:{DB_CONFIG['host']}")
CONN = db.connect_to_db(DB_CONFIG)
if CONN is not None:
    db.get_db_version(CONN)
else:
    logging.error(f"cannot connect to {DB_CONFIG['host']}")
    sys.exit(1)

#initialise cloudwatch client
CWM = aws.createClient(REGION,"cloudwatch")
RDS = aws.createClient(REGION,"rds")
RDS_ARN = aws.describe_rds_instance(RDS,DB_CONFIG['database'])
if RDS_ARN is not None:
    logging.info(f"cloudwatch logging configured for {RDS_ARN}")
    CW_LOGGING = True
else:
    logging.info(f"cloudwatch logging NOT configured for RDS instance:{DB_CONFIG['database']}")
    CW_LOGGING = False

@app.route("/api/<string:version>/health", methods=["GET"])
def health(version):
    if DB_HEALTH <= 3:
        return Response(json.dumps({"DB_errors":DB_HEALTH}, sort_keys=True), status=200, mimetype='application/json')
    else:
        return Response(json.dumps({"DB_errors":DB_HEALTH}, sort_keys=True), status=500, mimetype='application/json')



@app.route("/api/<string:version>/car/", methods=["POST"])
def add_new_car(version):
    global DB_HEALTH
    body = request.json
    if body is not None:
        try:
            reg = body['registration']
            make = body['make']
            model = body['make']
            colour = body['colour']
            capacity = body['capacity']
        except KeyError as e:
            logging.error(f'new car error: {str(e)}: {type(e)}')
            results = {"error": f"Incorrect Payload missing key {str(e)}"}
            status = 400
        else:
            car_details =[reg,make,model,colour,capacity]
            try:
                db.add_new_car(CONN,car_details)
            except Exception as e:
                if 'already exists.' in str(e):
                    logging.error(f'duplicate registration details {car_details[0]}')
                    status = 400
                    results = {"error": f'duplicate registration details {car_details[0]}'}
                else:
                    logging.error(f'error with car insert {str(e)}')
                    DB_HEALTH += 1
                    status = 500
                    results = {"error": 'something went wrong'}
                    if CW_LOGGING:
                        metric = "SLI-DB-Failed-Requests"
                        uri = "POST /car"
                        aws.put_cloudwatch_metric(CWM,metric,'pysimple',RDS_ARN,1,uri,'pysimple')
            else:
                logging.info(f"added new entry {car_details[0]}")
                status = 200
                results ={"success": status}
                if CW_LOGGING:
                        metric = "SLI-DB-Success-Requests"
                        uri = "POST /car"
                        aws.put_cloudwatch_metric(CWM,metric,'pysimple',RDS_ARN,1,uri,'pysimple')
    else:
        status = 400
        logging.error('missing payload')
        results = {"error": "empty payload"}
    return Response(json.dumps(results, sort_keys=True), status=status, mimetype='application/json')

@app.route("/api/<string:version>/car/<string:car_id>", methods=["PUT"])
def update_car(version,car_id):
    global DB_HEALTH
    reg = car_id
    body = request.json
    if body is not None:
        try:
            make = body['make']
            model = body['make']
            colour = body['colour']
            capacity = body['capacity']
        except KeyError as e:
            logging.error(f'new car error: {str(e)}: {type(e)}')
            results = {"error": f"Incorrect Payload missing key {str(e)}"}
            status = 400
        else:
            car_details = [reg, make, model, colour, capacity]
            try:
                rows = db.update_car(CONN,car_details)
            except Exception as e:
                logging.error(f'update error {str(e)}')
                DB_HEALTH += 1
                status = 500
                results = {"error": 'something went wrong'}
                if CW_LOGGING:
                    metric = "SLI-DB-Failed-Requests"
                    uri = "PUT /car"
                    aws.put_cloudwatch_metric(CWM, metric, 'pysimple', RDS_ARN, 1, uri, 'pysimple')
            else:
                if rows == 0:
                    logging.error(f"error: updated {rows} for entry {reg}")
                    status = 400
                    results = {"error": f"car {reg} not found"}
                else:
                    logging.info(f"updated {rows} for entry {reg}")
                    status = 200
                    results = {"success": status}
                    if CW_LOGGING:
                        metric = "SLI-DB-Success-Requests"
                        uri = "PUT /car"
                        aws.put_cloudwatch_metric(CWM, metric, 'pysimple', RDS_ARN, 1, uri, 'pysimple')
    else:
        status = 400
        logging.error('missing payload')
        results = {"error": "empty payload"}
    return Response(json.dumps(results, sort_keys=True), status=status, mimetype='application/json')


@app.route("/api/<string:version>/car/<string:car_id>", methods=["GET"])
def get_car(version,car_id):
    global DB_HEALTH
    try:
        results = db.get_car(CONN,car_id)
    except Exception as e:
        logging.error(f'failed to get registration details {car_id} error:{str(e)}')
        results = {}
        DB_HEALTH += 1
        status = 500
        if CW_LOGGING:
            metric = "SLI-DB-Failed-Requests"
            uri = "GET /car"
            aws.put_cloudwatch_metric(CWM, metric, 'pysimple', RDS_ARN, 1, uri, 'pysimple')
    else:
        logging.info(f"got entry for {car_id}")
        status = 200
        if CW_LOGGING:
            metric = "SLI-DB-Success-Requests"
            uri = "GET /car"
            aws.put_cloudwatch_metric(CWM, metric, 'pysimple', RDS_ARN, 1, uri, 'pysimple')
    return Response(json.dumps(results, sort_keys=True), status=status, mimetype='application/json')

@app.route("/api/<string:version>/cars/", methods=["GET"])
def get_cars(version):
    global DB_HEALTH
    try:
        results = db.get_cars(CONN)
    except Exception as e:
        logging.error(f'failed to get registration details  error:{str(e)}')
        results = {}
        DB_HEALTH += 1
        status = 500
    else:
        logging.info(f"got car list")
        status = 200
    return Response(json.dumps(results, sort_keys=True), status=status, mimetype='application/json')

@app.route("/api/<string:version>/cars/availble", methods=["GET"])
def get_availble_cars(version):
    global DB_HEALTH
    try:
        results = db.get_available_cars(CONN)
    except Exception as e:
        logging.error(f'failed to get list of available cars error:{str(e)}')
        results = {}
        DB_HEALTH += 1
        status = 500
    else:
        logging.info(f"got available car list")
        status = 200
    return Response(json.dumps(results, sort_keys=True), status=status, mimetype='application/json')

def update_car_availbility(conn,car_id,status):
    global DB_HEALTH
    try:
        result = db.update_car_availbility(conn,car_id,status)
    except Exception as e:
        DB_HEALTH += 1
        logging.error(f'failed to update car availbility {car_id}  error:{str(e)}')
        return {}
    else:
        logging.info(f"updated car availbility {car_id}:{status}")
        return result

@app.route("/api/<string:version>/booking/", methods=["POST"])
def add_booking(version):
    global DB_HEALTH
    body = request.json
    print(body)
    if body is not None:
        try:
            user_name = body['username']
            car_id = body['car_registration']
            pickup = body['pickup']
            drop_off = body['drop-off']
            booking_title = body['title']
            booking_description = body['description']
        except KeyError as e:
            logging.error(f'new booking error: {str(e)}: {type(e)}')
            results = {"error": f"Incorrect Payload missing key {str(e)}"}
            status = 400
        else:
            booking_details = [user_name, car_id, pickup, drop_off, booking_title, booking_description]
            try:
                booking_id = db.add_booking(CONN,booking_details)
            except Exception as e:
                logging.error(f'update error {str(e)}')
                DB_HEALTH += 1
                status = 500
                results = {"error": 'something went wrong'}
            else:
                logging.info(f"added new booking entry {booking_id}:{booking_description}")
                results = {"success" : booking_id}
                status = 200
    else:
        status = 400
        logging.error('missing payload')
        results = {"error": "empty payload"}
    return Response(json.dumps(results, sort_keys=True), status=status, mimetype='application/json')


@app.route("/api/<string:version>/bookings/", methods=["GET"])
def get_bookings(version):
    global DB_HEALTH
    try:
        results = db.get_bookings(CONN)
    except Exception as e:
        logging.error(f'failed to get list of bookings error:{str(e)}')
        DB_HEALTH += 1
        status = 500
        results = {}
    else:
        logging.info(f"got bookings list")
        status = 200
    return Response(json.dumps(results, sort_keys=True), status=status, mimetype='application/json')

@app.route("/api/<string:version>/booking/<string:booking_id>", methods=["GET"])
def get_booking(version,booking_id):
    global DB_HEALTH
    try:
        results = db.get_booking(CONN,booking_id)
    except Exception as e:
        logging.error(f'failed to get bookings error:{str(e)}')
        DB_HEALTH += 1
        status = 500
        results = {"error":"something went wrong"}
    else:
        logging.info(f"got bookings {booking_id}")
        status = 200
    return Response(json.dumps(results, sort_keys=True), status=status, mimetype='application/json')


@app.route("/api/<string:version>/admin/booking/approve/<string:booking_id>", methods=["PATCH"])
def approve_booking(version,booking_id):
    global DB_HEALTH
    try:
        results = db.approve_booking(CONN,booking_id)
    except Exception as e:
        logging.error(f'failed to approve bookings error:{str(e)}')
        status = 500
        DB_HEALTH += 1
        results = {"error": "something went wrong"}
    else:
        logging.info(f"approved bookings {booking_id}")
        results = {"success": 200}
        status = 200
    return Response(json.dumps(results, sort_keys=True), status=status, mimetype='application/json')

def main():
    logging.info(f"running {MODULE}")
    wsgi.server(listen(('', int(PORT))), app)

if __name__ == "__main__":
    main()