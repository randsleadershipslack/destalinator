#! /usr/bin/env python

def get_token(token, token_file):
    """
    if token, returns it
    if token is None, and token_file is not None,
    reads content of token_file and returns that
    if both are None, asserts an error
    """
    if token is None and token_file:
        f = open(token_file, "r")
        token = f.read().strip()
        f.close()
    assert token is not None
    return token
