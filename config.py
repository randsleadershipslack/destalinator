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
        if attrname == "slack_name":
            warnings.warn("The `slack_name` key in %s is deprecated in favor of the `SLACK_NAME` environment variable" %
                          self.config_fname, DeprecationWarning)

        return self.config[attrname]


# This deliberately isn't a `getenv` default so `.slack_name` isn't tried if there's a SLACK_NAME
SLACK_NAME = os.getenv("SLACK_NAME")
if SLACK_NAME is None:
    SLACK_NAME = Config().slack_name
