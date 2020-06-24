#!/usr/bin/env python
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core.context import Context
from aws_xray_sdk.ext.flask.middleware import XRayMiddleware
from aws_xray_sdk.core import patch_all
patch_all()


from flask import request, Response, redirect,abort,make_response,jsonify
from flask import Flask
from eventlet import wsgi, monkey_patch, listen
import logging
import os
import json
from configparser import ConfigParser
import awsHelper as cog
import decoder as jwt
import sys
import requests
from functools import wraps
#logging config
logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',level=logging.INFO,datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

#globals
MODULE = "widgets-auth"
HOST = "0.0.0.0"
PORT = "8000"
REDIRECT = f"http://127.0.0.1:{PORT}/api/v0.1/auth/login"
PROFILE = "default"
REGION = "eu-west-2"
PROFILE = "aws-dev"
REGION = "eu-west-2"
ENV="dev"
CONFIG_FILE = f"{ENV}_cfg.ini"

#initiliase flask
app = Flask(__name__)
app.secret_key = os.urandom(24)
cidp = cog.createClient(REGION,"cognito-idp")
xray_recorder.configure(
    sampling=False,
    context_missing='LOG_ERROR',
    service='pyapp',
    context=Context()
)
XRayMiddleware(app, xray_recorder)


def check_token(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        allowed = False
        keys = USER_POOL['keys']
        idtoken = request.cookies.get("idtoken")
        atoken = request.cookies.get("access_token")
        if idtoken == None and atoken == None:
            return abort(400, description="no identity or access token")
        if idtoken != None:
            i_tokenObject = jwt.decode_cognito_token(idtoken, COGNITO_CFG['client_id'], keys)
            if 'error' in i_tokenObject:
                logging.error('failed admin pool token auth, generating error')
                result = {'error': "token not valid", "result": "fail"}
                return abort(401, description="invalid id_token")
        if atoken != None:
            a_tokenObject = jwt.decode_cognito_token(atoken, COGNITO_CFG['client_id'], keys)
            if 'error' in a_tokenObject:
                logging.error('failed admin pool token auth, generating error')
                result = {'error' : "token not valid", "result": "fail"}
                return abort(401,description="invalid access_token")
        action = request.method
        resource = request.endpoint
        resource_url = request.base_url
        user_pool_id = str(i_tokenObject['data']['iss']).split("/")[-1]
        first_group = i_tokenObject['data']['cognito:groups'][0]
        inferred_scope = f"{first_group}.{resource}.{action}"
        resource_response = cog.decribe_rs(cidp, user_pool_id, resource_url)
        try:
            error = resource_response['error']
        except Exception as e:
            logging.info(f"checking {inferred_scope} in {resource_response['ResourceServer']['Scopes']}")
            for scope in resource_response['ResourceServer']['Scopes']:
                if scope['ScopeName'] == inferred_scope:
                    logging.info('matched inferred scope')
                    allowed = True
        else:
            if "ResourceNotFoundException" in resource_response['error']:
                logging.info(f"not a protect resource:passing")
                allowed = True
            else:
                logging.info(f"error for resource:{error}")
                allowed = True
        if allowed:
            return f(*args, **kwargs)
        else:
            return abort(403, description="Inferred permission denied")
    return wrap

def get_keys(url):
    try:
        result = requests.get(url, timeout=1)
    except Exception as e:
        logging.error(f'failed to get userpool JWK {str(e)}')
        raise e
    else:
        logging.debug(result.json())
        return result.json()

def get_config(filename,section):
    parser = ConfigParser()
    parser.read(filename)
    config = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            config[param[0]] = param[1]
        logging.info(f"added config section {section} from {filename}")
    else:
        logging.error(f'Section {section} not found in the {filename} file')
        sys.exit(1)
    return config

USER_POOL = get_config(CONFIG_FILE, "user_user_pool")
USER_POOL['keys'] = get_keys(USER_POOL['key_url'])
USER_POOL_ID = USER_POOL['id']
COGNITO_CFG = get_config(CONFIG_FILE, "cognito_app")

@app.route('/api/<string:version>/auth/login',methods=["POST"])
@xray_recorder.capture('login')
def loginUser(version):
    user_pool = "admins"
    result = {}
    headers = {}
    username = request.authorization.username
    password = request.authorization.password
    authObject = cog.login(cidp,username,password,user_pool,COGNITO_CFG['client_id'],COGNITO_CFG['client_secret'])
    if 'error' in authObject:
        if 'User is disabled' in str(authObject['error']):
            result['error'] = "user disabled"
        else:
            result['error'] = str(authObject['error'])
        status = 401
        result['result'] = 'fail'
    else:
        result['result'] = "ok"
        result['data'] = authObject['AuthenticationResult']
        status = 200
    lresponse = Response(json.dumps(result), status=status, mimetype='application/json',headers=headers)
    if status == 200:
        lresponse.set_cookie("idtoken",authObject['AuthenticationResult']['IdToken'],httponly=True,expires=None)
        lresponse.set_cookie("atoken", authObject['AuthenticationResult']['AccessToken'], httponly=True, expires=None)
    return lresponse


@app.route('/api/<string:version>/auth/whoami',methods=["GET"])
@xray_recorder.capture('whoami')
@check_token
def whoami(version):
    user_pool_id = USER_POOL['id']
    keys = USER_POOL['keys']
    headers = {}
    idtoken = request.cookies.get("idtoken")
    accesstoken = request.cookies.get("atoken")
    i_tokenObject =  jwt.decode_cognito_token(idtoken,COGNITO_CFG['client_id'],keys)
    a_tokenObject = jwt.decode_cognito_token(accesstoken, COGNITO_CFG['client_id'], keys)
    user_pool_id = str(i_tokenObject['data']['iss']).split("/")[-1]
    result = { 'result' : "ok", "data": {"id": i_tokenObject, "access" : a_tokenObject}, "userpool": user_pool_id }
    status = 200
    return Response(json.dumps(result), status=status, mimetype='application/json',headers=headers)

@app.route('/api/<string:version>/auth/resource',methods=["GET"])
@check_token
@xray_recorder.capture('resource_server_check')
def resource_servers(version):
    headers = {}
    user_pool_id = USER_POOL['id']
    keys = USER_POOL['keys']
    resource_type = request.args.get('type')
    idtoken = request.cookies.get("idtoken")
    tokenObject = jwt.decode_cognito_token(idtoken, COGNITO_CFG['client_id'], keys)
    user_pool_id = str(tokenObject['data']['iss']).split("/")[-1]
    resource = cog.decribe_rs(cidp,user_pool_id,resource_type)
    result = { 'result' : "ok", "data": resource }
    status = 200
    return Response(json.dumps(result), status=status, mimetype='application/json',headers=headers)

@app.route('/api/<string:version>/protected',methods=["GET"])
@check_token
@xray_recorder.capture('protected')
def protected(version):
    headers = {}
    result ={"result":"ok"}
    user_pool_id = USER_POOL['id']
    keys = USER_POOL['keys']
    status = 200
    return Response(json.dumps(result), status=status, mimetype='application/json',headers=headers)

@app.route('/api/<string:version>/auth/signout',methods=["DELETE"])
@check_token
def signout(version):
    headers = {}
    user_pool_id = USER_POOL['id']
    keys = USER_POOL['keys']
    idtoken = request.cookies.get("idtoken")
    tokenObject = jwt.decode_cognito_token(idtoken, COGNITO_CFG['client_id'], keys)
    username = tokenObject['data']['cognito:username']
    signout_response = cog.admin_signout(cidp, user_pool_id, username)
    try:
        error = signout_response['error']
    except Exception as e:
        logging.info(f"{username}signed out ")
        status = 200
        result = {"result": "ok"}
    else:
        status = 500
        logging.error(f"failed to sign out {username} with {error}")
        result = {"error": error}
    return Response(json.dumps(result), status=status, mimetype='application/json',headers=headers)

@app.route('/api/<string:version>/welcome',methods=["GET"])
def home(version):
    headers = {}
    result = "<HTML><head>Welcome to cars</head></HTML>"
    user_pool_id = USER_POOL['id']
    keys = USER_POOL['keys']
    status = 200
    return Response(result, status=status, mimetype='text/html',headers=headers)



def main():
    logging.info(f"running {MODULE}")
    wsgi.server(listen(('', int(PORT))), app)
    #app.run(host='0.0.0.0', port=PORT)


if __name__ == "__main__":
    main()


