"""Error generation and handling"""

ERROR_CODES = {
    0: 'Missing parameter',
    1: 'Error processing authentication credentials',
    2: 'Verification of credentials failed',
    3: 'Network error',
    4: 'Application verification failed',
}

def error_dict(error_code):
    """Generates an Error dict suitable for storing in a key/value store."""
    err = {'status': 'fail'}
    err['reason'] = {'code': error_code,
                     'description': ERROR_CODES[error_code]}
    return err
