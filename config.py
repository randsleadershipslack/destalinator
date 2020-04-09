#! /usr/bin/env python

import os
import yaml

from utils.with_logger import WithLogger


class Config(WithLogger):
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
            self.logger.warning("The `%s` environment variable is deprecated in favor of the `DESTALINATOR_%s` environment variable", upper_attrname, upper_attrname)
        else:
            envvar = os.getenv('DESTALINATOR_' + upper_attrname)
            self.logger.debug("env var [%s] value: [%s]", attrname, envvar)
        if envvar is not None:
            split_envvar = [x.strip() for x in envvar.split(',') if x] if ',' in envvar else envvar
            self.logger.debug("env var [%s] found, and split to: %s", attrname, split_envvar)
            return split_envvar

        file_based_config = self.config.get(attrname, '')
        self.logger.debug("using file based config for: [%s] with value [%s]", attrname, file_based_config or "")
        return file_based_config

    def get(self, attrname, fallback=None):
        return self.config.get(attrname, fallback)


_config = Config()


def get_config():
    return _config


class WithConfig(object):
    @property
    def config(self):
        return get_config()
