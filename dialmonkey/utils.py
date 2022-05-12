#!/usr/bin/env python3

import pydoc
from typing import TypeVar, Callable

import yaml
T = TypeVar('T')


def load_conf(conf_path: str) -> dict:
    """
    Loads the configuration from provided YAML file.
    :param conf_path: path to the configuration file
    :return: configuration loaded as dict
    """
    with open(conf_path, 'rt') as in_fd:
        conf = yaml.load(in_fd, Loader=yaml.FullLoader)
    return conf


def dynload_class(path: str) -> Callable:
    """
    Locates and imports a class reference that is provided.
    :param path: A location of the class being imported (package.module.path.file.ClassName)
    :return: A reference to the class provided or None if not found.
             The operator `()` can be called on the returned value.
    """
    cls = pydoc.locate(path)
    return cls


class dotdict(dict):

    def __init__(self, dct=None):
        if dct is not None:
            dct = dotdict.transform(dct)
        else:
            dct = {}
        super(dotdict, self).__init__(dct)

    @staticmethod
    def transform(dct):
        new_dct = {}
        for k, v in dct.items():
            if isinstance(v, dict):
                new_dct[k] = dotdict(v)
            else:
                new_dct[k] = v
        return new_dct

    __getattr__ = dict.__getitem__

    def __setitem__(self, key, value):
        if isinstance(value, dict):
            super(dotdict, self).__setitem__(key, dotdict(value))
        else:
            super(dotdict, self).__setitem__(key, value)

    def __setattr__(self, key, value):
        self[key] = value

    __delattr__ = dict.__delitem__

    def __getstate__(self):
        result = self.__dict__.copy()
        return result

    def __setstate__(self, dict):
        self.__dict__ = dict
