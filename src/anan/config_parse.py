# -*- coding: utf-8 -*-

from yaml import load as yaml_load
import logging


def get_config(filename):
    try:
        config = yaml_load(file(filename).read()) # NOQA
        return config
    except Exception as e:
        logging.error(e, exc_info=True)
        return []
