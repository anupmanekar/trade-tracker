import hmac
import base64
import json
import time

def get_timestamp():
  return int(time.time() * 1000)

def sign(message, secret_key):
  mac = hmac.new(bytes(secret_key, encoding='utf8'), bytes(message, encoding='utf-8'), digestmod='sha256')
  d = mac.digest()
  return base64.b64encode(d)

def pre_hash(timestamp, method, request_path, body):
  return str(timestamp) + str.upper(method) + request_path + body

def parse_params_to_str(params):
    params = [(key, val) for key, val in params.items()]
    params.sort(key=lambda x: x[0])
    url = '?' +toQueryWithNoEncode(params);
    if url == '?':
        return ''
    return url

def toQueryWithNoEncode(params):
    url = ''
    for key, value in params:
        url = url + str(key) + '=' + str(value) + '&'
    return url[0:-1]

def generate_signature(api_secret_key, timestamp, method, request_path, params=None, body=None):
    """
    Generate Bitget API signature.

    Args:
        api_secret_key (str): API secret key.
        timestamp (str or int): Timestamp in milliseconds.
        method (str): HTTP method (GET, POST, etc.).
        request_path (str): API endpoint path.
        params (dict, optional): Query or body parameters.
        body (dict or str, optional): POST body (dict or str).

    Returns:
        str: Base64-encoded signature.
    """
    if method.upper() == "GET":
        body_str = ""
        if params:
            request_path = request_path + parse_params_to_str(params)
    else:
        body_str = body if body else ""
    prehash = pre_hash(timestamp, method, request_path, body_str)
    print(f"Prehash string: {prehash}")
    signature = sign(prehash, api_secret_key)
    return signature