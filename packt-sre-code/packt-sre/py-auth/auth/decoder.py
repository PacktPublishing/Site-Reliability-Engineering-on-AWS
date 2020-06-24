#!/usr/bin/env python
import logging
import time
from jose import jwk, jwt
from jose.utils import base64url_decode
import json


def decode_cognito_token(token,cognito_clinet_id,aws_keys):
    result = {}
    try:
        headers = jwt.get_unverified_headers(token)
    except Exception as e:
        result = {"error": str(e)}
        logging.error(result)
        return result
    else:
        logging.info(json.dumps(headers))
        id_kid = headers['kid']
        logging.info(f'kid:{id_kid} found in idtoken')
    # search for the kid in the downloaded public keys
    key_index = -1
    for count in range(len(aws_keys['keys'])):
        if aws_keys['keys'][count]['kid'] == id_kid:
            logging.info(f"matched idtoken kid with AWS kid index:{count}")
            key_index=count
    if key_index == -1:
        logging.error('Public key not found in jwks.json')
        result = {"error":"Public key not found in jwks.json"}
        return result
    # construct the public key
    public_key = jwk.construct(aws_keys['keys'][key_index])
    # get the last two sections of the token,
    # message and signature (encoded in base64)
    message, encoded_signature = str(token).rsplit('.', 1)
    # decode the signature
    decoded_signature = base64url_decode(encoded_signature.encode('utf-8'))
    # verify the signature
    if not public_key.verify(message.encode("utf8"), decoded_signature):
        logging.error('Signature verification failed')
        result = {"error": "Signature verification failed"}
        return result
    logging.info('Signature successfully verified')
    # since we passed the verification, we can now safely
    # use the unverified claims
    claims = jwt.get_unverified_claims(token)
    # additionally we can verify the token expiration
    if time.time() > claims['exp']:
        logging.error('Token has expired')
        result = {"error": "Token has expired"}
        return result
    # and the Audience  (use claims['client_id'] if verifying an access token)
    if claims['token_use'] == 'id':
        if claims['aud'] != cognito_clinet_id:
            logging.error('Token was not issued for this audience')
            result = {"error": "Token was not issued for this audience"}
            return result
    if claims['token_use'] == 'access':
        if claims['client_id'] != cognito_clinet_id:
            logging.error('Token was not issued for this audience')
            result = {"error": "Token was not issued for this audience"}
            return result

    result['data'] = claims
    return result
    ''''''