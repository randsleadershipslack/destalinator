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

        upper_attrname = attrname.upper()
        envvar = os.getenv(upper_attrname)
        if envvar is not None:
            warnings.warn("The %s environment variable is deprecated in favor of the `DESTALINATOR_%s` environment variable".format(upper_attrname, upper_attrname), DeprecationWarning)
        else:
            envvar = os.getenv('DESTALINATOR_' + upper_attrname)
        if envvar is not None:
            return envvar.split(',') if ',' in envvar else envvar

        return self.config.get(attrname, '')

    def get(self, attrname, fallback=None):
        return self.config.get(attrname, fallback)
