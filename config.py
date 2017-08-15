#! /usr/bin/env python

import os
import warnings
import yaml


class Config(object):
    config_fname = "configuration.yaml"

    def __init__(self, config_fname=None):
        config_fname = config_fname or self.config_fname
        fo = open(config_fname, "r")
        blob = fo.read()
        fo.close()
        self.config = yaml.load(blob)

    def __getattr__(self, attrname):
        envvar = os.getenv('DESTALINATOR_' + attrname.upper())
        if envvar is not None:
            return envvar.split(',') if ',' in envvar else envvar

        return self.config.get(attrname, '')

    def get(self, attrname, fallback=None):
        return self.config.get(attrname, fallback)
