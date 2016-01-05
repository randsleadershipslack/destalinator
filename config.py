#! /usr/bin/env python

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
        return self.config[attrname]
