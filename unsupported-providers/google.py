"""This module exists as a bw-compat shim for google_hybrid."""
from .google_hybrid import (
    add_google_login,
    GoogleAuthenticationComplete,
)

def includeme(config):
    config.add_directive('add_google_login', add_google_login)
