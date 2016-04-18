#! /usr/bin/env python

import os


def get_token(token, token_file, token_env_variable):
    """
    if token, returns it
    if token is None, and token_file is not None,
    reads content of token_file and returns that
    If token is None, token_file is None, and token_env_variable is not None,
    return the value of that.
    if all are None (or empty), asserts an error
    """
    if token is None and token_file:
        f = open(token_file, "r")
        token = f.read().strip()
        f.close()
    if token is None and token_file is None and token_env_variable:
        token = os.getenv(token_env_variable)
        if token == "":
            token = None
    assert token is not None
    return token
