# -*- coding: utf-8 -*-
# Standard Library
import contextlib
import importlib

MODULES = ("orjson", "ujson")

mainjson = None

__all__ = ["dump", "dumps", "load", "loads"]

backup_dumps = None
backup_dump = None
backup_loads = None
backup_load = None


def dumps(obj, **kw):
    output = mainjson.dumps(obj)
    with contextlib.suppress(AttributeError):
        output = output.decode("utf-8")
    return output


def loads(obj, **kw):
    return mainjson.loads(obj)


def dump(obj, fp, **kw):
    return fp.write(dumps(obj))


def load(fp, **kw):
    data = fp.read()
    return mainjson.loads(data)


def import_modules():
    for name in MODULES:
        with contextlib.suppress(Exception):
            yield importlib.import_module(name)


MODULES_IMPORTS = list(import_modules())
MODULES_NAME = [module.__name__ for module in MODULES_IMPORTS]

for item in MODULES:
    with contextlib.suppress(ValueError):
        index = MODULES_NAME.index(item)
        mainjson = MODULES_IMPORTS[index]
        if mainjson:
            break
