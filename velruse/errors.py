"""Error generation and handling"""
from velruse.utils import json

ERROR_CODES = {
    0: 'Missing parameter',
    1: 'Error processing authentication credentials',
    2: 'Verification of credentials failed',
    3: 'Network error',
}

def error_string(error_code):
    """Generates an Error string suitable for storing in a
    key/value store using simplejson"""
    err = {'status': 'fail'}
    err['reason'] = {'code': error_code, 
                     'description': ERROR_CODES[error_code]}
    return json.dumps(err)
