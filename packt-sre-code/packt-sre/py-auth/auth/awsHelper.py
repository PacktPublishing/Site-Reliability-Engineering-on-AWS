#!/usr/bin/env python
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all
patch_all()
import boto3
from os import environ
import logging
import random
import string
import hmac, base64, hashlib
import requests
import decoder as dec
from configparser import ConfigParser
import sys


# logging config
logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',level=logging.INFO,datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

# globals
MODULE = "cognito-helper"
PROFILE = "default"
REGION = "eu-west-2"
ENV="dev"
CONFIG_FILE = f"{ENV}_cfg.ini"

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

def get_keys(url):
    try:
        result = requests.get(url, timeout=1)
    except Exception as e:
        logging.error(f'failed to get userpool JWK {str(e)}')
        raise e
    else:
        logging.info(result.json())
        return result.json()

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



def get_scope_auth(scope,client_id):
    url = "https://auth.internetwidget.com/oauth2/authorize"
    query_params = {"response_type":"token","client_id":client_id,"redirect_uri":"https://localhost/login","scope":scope,"state":"STATE"}
    try:
        r = requests.get(url,params=query_params)
        print(r.status_code)
    except ConnectionError as e:
        result = {"error":e}
        print(e)
    except Exception as e:
        result = {"error": e}
        print(e)
    else:
        print(r)
    print(r.url)
    return


def gen_password(stringLength):
    password_characters = string.ascii_letters + string.digits + "!£$%&#"
    result = ''.join(random.choice(password_characters) for i in range(stringLength))
    return result


def get_mac_digest(username, clientid, clientsecret):
    msg = username + clientid
    dig = hmac.new(str(clientsecret).encode('utf-8'),msg=str(msg).encode('utf-8'), digestmod=hashlib.sha256).digest()
    signature = base64.b64encode(dig).decode()
    return signature


def decribe_rs(client,poolid,resource):
    result = {}
    try:
        result = client.describe_resource_server(UserPoolId=poolid,Identifier=resource)
    except Exception as e:
        result = {"error": str(e)}
    return result

def admin_signout(client,poolid,username):
    result = {}
    try:
        result = client.admin_user_global_sign_out(UserPoolId=poolid, Username=username)
    except Exception as e:
        result = {"error": str(e)}
    return result


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


def admin_auth(client,clientid,clientsecret,poolid,username,password):
    auth = "USER_PASSWORD_AUTH"
    hash = get_mac_digest(username,clientid,clientsecret)
    try:
        result = client.initiate_auth(ClientMetadata={"UserPoolId":poolid},ClientId=clientid, \
                AuthFlow=auth,AuthParameters={'USERNAME':username,"PASSWORD":password,"SECRET_HASH":hash})
    except Exception as e:
        logging.error('error:{}'.format(e))
        result = {"error": e}
    else:
        logging.info("result:{}".format(result))
    return result


def password_challenge(client,clientid,clientsecret,poolid,username,sessionid):
    challenge = "NEW_PASSWORD_REQUIRED"
    secret_hash = get_mac_digest(username,clientid,clientsecret)
    password = gen_password(20)
    logging.info(f"challenge response {clientid}:{clientsecret}:{poolid}:{username}:{secret_hash}")
    try:
        result = client.admin_respond_to_auth_challenge(UserPoolId=poolid,ClientId=clientid, \
        Session=sessionid, ChallengeName=challenge,ChallengeResponses={'NEW_PASSWORD':password,"USERNAME":username,"SECRET_HASH":secret_hash})
    except Exception as e:
        logging.error('error:{}'.format(e))
        result = {"error": e}
    else:
        print("user:{} new_password:{}".format(username, password))
    return result, password


def login(client,user,password,pool,client_id,client_secret):
    try:
        result = admin_auth(client, client_id, client_secret, pool, user, password)
    except Exception as e:
        logging.error(f"failed on auth error:{str(e)}")
        return {"auth_error":str(e)}
    else:
        if "ChallengeName" in result:
            if result['ChallengeName'] == "NEW_PASSWORD_REQUIRED":
                logging.info(f"new password required for session ")
                try:
                    new_pass_result, new_password = password_challenge(client, client_id, client_secret, pool, user,result['Session'])
                except Exception as e:
                    result = {"on initial login error":str(e)}
                    logging.error(f'failed to auth using old password {str(e)} new password required')
                else:
                    try:
                        result = admin_auth(client, client_id, client_secret, pool, user, new_password)
                    except Exception as e:
                        logging.error(f'error with 2nd auth after new password {str(e)}')
                        result = {"on 2nd login error": str(e)}
    return result


def main ():
    print('Running:{}'.format(MODULE))
    USER_POOL = get_config(CONFIG_FILE, "user_user_pool")
    USER_POOL['keys'] = get_keys(USER_POOL['key_url'])
    USER_POOL_ID = USER_POOL['id']
    COGNITO_CFG = get_config(CONFIG_FILE, "cognito_app")
    cidp = createClient(REGION,'cognito-idp')

    user = "kevin@internetwidget.com"
    password = r'9YSRTvVJDI75&!7£tUtf'
    login_result = login(cidp,user,password,USER_POOL_ID,COGNITO_CFG['client_id'],COGNITO_CFG['client_secret'])
    decode_idresult = dec.decode_cognito_token(login_result['AuthenticationResult']['IdToken'],COGNITO_CFG['client_id'],USER_POOL['keys'] )
    print(decode_idresult)
    get_scope_auth("http://api.internetwidget.com/api/v0.1/car.read",COGNITO_CFG['client_id'])


if __name__ == "__main__":
    main()

